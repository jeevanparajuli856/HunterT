#!/usr/bin/env python3
"""Count live vs dead domains from the provided LSTM datasets.

Default source uses LM-training split files:
- train/train.csv
- validation/validation.csv
- test/test.csv

Optionally, you can use combined_dataset.csv with --source combined.
"""

import argparse
import csv
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, Set, Tuple
from urllib import error, request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Count live/dead domains in dataset")
    parser.add_argument(
        "--source",
        choices=["lm", "combined"],
        default="lm",
        help="Dataset source to check (default: lm)",
    )
    parser.add_argument(
        "--root",
        default="/home/jeevan/HunterT/LTSM_Research/datasets",
        help="Root path for datasets",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=6.0,
        help="HTTP timeout per request in seconds (default: 6)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=48,
        help="Parallel workers (default: 48)",
    )
    return parser.parse_args()


def filename_to_domain(filename: str) -> str:
    s = filename.strip()
    if s.endswith(".csv"):
        s = s[:-4]

    if s.startswith("https__"):
        s = s[len("https__") :]
    elif s.startswith("http__"):
        s = s[len("http__") :]

    # Dataset uses underscores where slashes would be, often trailing underscore.
    s = s.replace("_", "/").strip("/")
    return s


def domains_from_lm(root: Path) -> Set[str]:
    files = [
        root / "LM-training-datasets" / "train" / "train.csv",
        root / "LM-training-datasets" / "validation" / "validation.csv",
        root / "LM-training-datasets" / "test" / "test.csv",
    ]

    domains: Set[str] = set()
    for path in files:
        with path.open(newline="", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                filename = (row.get("Filename") or "").strip()
                if not filename:
                    continue
                domain = filename_to_domain(filename)
                if domain:
                    domains.add(domain)
    return domains


def domains_from_combined(root: Path) -> Set[str]:
    path = root / "combined_dataset" / "combined_dataset.csv"
    domains: Set[str] = set()

    with path.open(newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = (row.get("Domain") or "").strip()
            if domain:
                domains.add(domain)

    return domains


def probe_domain(domain: str, timeout: float) -> Tuple[str, bool]:
    # Consider domain live if any HTTP(S) response is received.
    # 4xx/5xx still indicate host is reachable.
    headers = {"User-Agent": "Mozilla/5.0 (compatible; LiveDeadChecker/1.0)"}
    urls = [f"https://{domain}", f"http://{domain}"]

    for url in urls:
        req = request.Request(url, headers=headers, method="GET")
        try:
            with request.urlopen(req, timeout=timeout):
                return domain, True
        except error.HTTPError:
            return domain, True
        except (error.URLError, TimeoutError, socket.timeout, ValueError):
            continue
        except Exception:
            continue

    return domain, False


def main() -> None:
    args = parse_args()
    root = Path(args.root)

    if args.source == "lm":
        domains = domains_from_lm(root)
    else:
        domains = domains_from_combined(root)

    live = 0
    dead = 0

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = [pool.submit(probe_domain, d, args.timeout) for d in domains]
        for future in as_completed(futures):
            _, ok = future.result()
            if ok:
                live += 1
            else:
                dead += 1

    print(f"TOTAL_UNIQUE_DOMAINS={len(domains)}")
    print(f"LIVE={live}")
    print(f"DEAD={dead}")


if __name__ == "__main__":
    main()
