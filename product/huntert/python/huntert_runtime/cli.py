"""CLI entrypoint for the HunterT Python runtime backend."""

from __future__ import annotations

import argparse
import json
import sys

from .bundle import inspect_bundle
from .export_bundle import export_bundle
from .sidecar import main as run_sidecar


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="huntert_runtime",
        description="Python sidecar and bundle tooling for HunterT.",
    )
    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser("serve", help="run the stdio JSON prediction sidecar")
    serve_parser.add_argument("--bundle", help="optional bundle directory to load on startup")

    bundle_parser = subparsers.add_parser("bundle", help="bundle operations")
    bundle_subparsers = bundle_parser.add_subparsers(dest="bundle_command")

    inspect_parser = bundle_subparsers.add_parser("inspect", help="inspect a bundle")
    inspect_parser.add_argument("--bundle", required=True, help="bundle directory")

    export_parser = bundle_subparsers.add_parser(
        "export-default",
        help="export the curated default runtime bundle from the research assets",
    )
    export_parser.add_argument("--bundle", required=True, help="destination bundle directory")
    export_parser.add_argument("--model", help="source model checkpoint")
    export_parser.add_argument("--train-data-dir", help="training dataset directory")
    export_parser.add_argument("--wordlist", help="source wordlist")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "serve":
        return run_sidecar(args.bundle)
    if args.command == "bundle" and args.bundle_command == "inspect":
        payload = inspect_bundle(args.bundle)
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if args.command == "bundle" and args.bundle_command == "export-default":
        payload = export_bundle(
            model_path=args.model,
            train_data_dir=args.train_data_dir,
            wordlist_path=args.wordlist,
            output_dir=args.bundle,
        )
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    parser.print_help()
    return 0
