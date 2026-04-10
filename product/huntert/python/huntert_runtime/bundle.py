"""Bundle loading and LSTM inference helpers."""

from __future__ import annotations

import json
from pathlib import Path
import re
from dataclasses import dataclass
from typing import Any

import torch

from .model import LSTM
from .vocab import RuntimeVocab

YEAR_PATTERN = re.compile(r"^\d{4}$")


@dataclass(slots=True)
class LoadedBundle:
    bundle_dir: Path
    manifest: dict[str, Any]
    model: LSTM
    vocab: RuntimeVocab
    device: torch.device
    wordlist_count: int

    @property
    def model_info(self) -> dict[str, Any]:
        return dict(self.manifest.get("model", {}))


def resolve_bundle_path(bundle_path: str | Path) -> Path:
    path = Path(bundle_path).expanduser().resolve()
    if path.is_file():
        return path.parent
    return path


def load_manifest(bundle_path: str | Path) -> tuple[dict[str, Any], Path]:
    bundle_dir = resolve_bundle_path(bundle_path)
    manifest_path = bundle_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"bundle manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for rel_path in (
        manifest["files"]["model"],
        manifest["files"]["vocab"],
        manifest["files"]["wordlist"],
    ):
        if not (bundle_dir / rel_path).exists():
            raise FileNotFoundError(f"bundle file not found: {bundle_dir / rel_path}")
    return manifest, bundle_dir


def load_bundle(bundle_path: str | Path) -> LoadedBundle:
    manifest, bundle_dir = load_manifest(bundle_path)
    vocab_payload = json.loads((bundle_dir / manifest["files"]["vocab"]).read_text(encoding="utf-8"))
    tokens = vocab_payload["tokens"]
    vocab = RuntimeVocab(tokens=tokens, default_index=vocab_payload.get("default_index", 0))

    model_info = manifest["model"]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = LSTM(
        vocab_size=len(vocab),
        embedding_dim=int(model_info["embedding_size"]),
        hidden_dim=int(model_info["embedding_size"]),
        num_layers=int(model_info["num_layers"]),
        dropout_rate=float(model_info["dropout_rate"]),
        tie_weights=True,
    ).to(device)

    state_dict = torch.load(bundle_dir / manifest["files"]["model"], map_location=device)
    model.load_state_dict(state_dict)
    model.eval()

    wordlist_count = count_wordlist_entries(bundle_dir / manifest["files"]["wordlist"])
    return LoadedBundle(
        bundle_dir=bundle_dir,
        manifest=manifest,
        model=model,
        vocab=vocab,
        device=device,
        wordlist_count=wordlist_count,
    )


def inspect_bundle(bundle_path: str | Path) -> dict[str, Any]:
    manifest, bundle_dir = load_manifest(bundle_path)
    vocab_payload = json.loads((bundle_dir / manifest["files"]["vocab"]).read_text(encoding="utf-8"))
    wordlist_count = count_wordlist_entries(bundle_dir / manifest["files"]["wordlist"])
    return {
        "id": manifest.get("id", ""),
        "bundle_dir": str(bundle_dir),
        "manifest": manifest,
        "vocab_size": len(vocab_payload["tokens"]),
        "wordlist_count": wordlist_count,
    }


def count_wordlist_entries(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1", errors="ignore")
    return len([line for line in text.splitlines() if line.strip()])


def normalize_token(token: str) -> str:
    return "YEAR" if YEAR_PATTERN.match(token) else token


def predict_next(bundle: LoadedBundle, tokens: list[str], top_k: int) -> dict[str, Any]:
    raw_sequence = list(tokens) or ["<sos>"]
    sequence = [normalize_token(token) for token in raw_sequence]
    if sequence[0] != "<sos>":
        raw_sequence = ["<sos>"] + raw_sequence
        sequence = ["<sos>"] + sequence

    oov_tokens = sorted(
        {
            raw
            for raw, normalized in zip(raw_sequence, sequence)
            if not raw.startswith("<") and normalized not in bundle.vocab
        }
    )

    indices = [bundle.vocab[token] for token in sequence]
    hidden = bundle.model.init_hidden(batch_size=1, device=bundle.device)

    with torch.no_grad():
        src = torch.tensor([indices], dtype=torch.long, device=bundle.device)
        prediction, _ = bundle.model(src, hidden)
        logits = prediction[:, -1, :]

        for special in ("<eos>", "<sos>", "<unk>", "<pad>"):
            logits[:, bundle.vocab[special]] = -float("inf")

        probs = torch.softmax(logits, dim=-1)
        limit = min(top_k, probs.shape[-1])
        top_probs, top_indices = torch.topk(probs, limit)
        itos = bundle.vocab.get_itos()

        candidates = [
            {"token": itos[index.item()], "prob": float(prob.item())}
            for prob, index in zip(top_probs[0], top_indices[0])
        ]

    return {"candidates": candidates, "oov_tokens": oov_tokens}
