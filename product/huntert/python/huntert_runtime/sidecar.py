"""Long-lived stdio JSON sidecar for HunterT LSTM inference."""

from __future__ import annotations

import json
import sys
from typing import Any

from .bundle import inspect_bundle, load_bundle, predict_next


class Server:
    """Serve JSON-line requests from stdin and emit JSON-line responses."""

    def __init__(self, bundle_path: str | None = None) -> None:
        self._bundle = load_bundle(bundle_path) if bundle_path else None

    def serve(self) -> int:
        for raw_line in sys.stdin:
            line = raw_line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
                response, should_exit = self._handle(request)
            except Exception as exc:  # pragma: no cover - protocol guard
                response = {"ok": False, "error": str(exc)}
                should_exit = False

            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()
            if should_exit:
                return 0
        return 0

    def _handle(self, request: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        operation = str(request.get("op", "")).strip()

        if operation == "load_bundle":
            bundle_path = str(request.get("bundle_path", "")).strip()
            if not bundle_path:
                raise ValueError("load_bundle requires bundle_path")
            self._bundle = load_bundle(bundle_path)
            return {"ok": True, "bundle": inspect_bundle(bundle_path)}, False

        if operation == "inspect_bundle":
            if self._bundle is not None:
                return {
                    "ok": True,
                    "bundle": {
                        "id": self._bundle.manifest.get("id", ""),
                        "bundle_dir": str(self._bundle.bundle_dir),
                        "manifest": self._bundle.manifest,
                        "vocab_size": len(self._bundle.vocab),
                        "wordlist_count": self._bundle.wordlist_count,
                    },
                }, False

            bundle_path = str(request.get("bundle_path", "")).strip()
            if not bundle_path:
                raise RuntimeError("no bundle is loaded")
            return {"ok": True, "bundle": inspect_bundle(bundle_path)}, False

        if operation == "predict_next":
            if self._bundle is None:
                raise RuntimeError("no bundle is loaded")
            tokens = [str(token) for token in request.get("tokens", [])]
            top_k = int(request.get("top_k", 128))
            return {"ok": True, "candidates": predict_next(self._bundle, tokens, top_k)}, False

        if operation == "shutdown":
            return {"ok": True}, True

        raise ValueError(f"unsupported operation: {operation}")


def main(bundle_path: str | None = None) -> int:
    return Server(bundle_path=bundle_path).serve()
