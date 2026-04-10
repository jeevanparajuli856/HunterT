"""Export a curated HunterT runtime bundle from the research pipeline."""

from __future__ import annotations

import hashlib
import shutil
import sys
from datetime import datetime, timezone
import json
from pathlib import Path

from . import __version__

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_MODEL = REPO_ROOT / "Research" / "lstm_pipeline" / "saved_models" / "model_MD10_MF5_es128_nl2_dr0.2_loss3.319183.pt"
DEFAULT_TRAIN_DATA = REPO_ROOT / "Research" / "LSTM_Research" / "datasets" / "LM-training-datasets"
DEFAULT_WORDLIST = REPO_ROOT / "Research" / "LSTM_Research" / "chosen_wordlists" / "big_wfuzz.txt"
DEFAULT_OUTPUT = REPO_ROOT / "product" / "huntert" / "runtime" / "bundles" / "default"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_bundle(
    *,
    model_path: str | Path | None = None,
    train_data_dir: str | Path | None = None,
    wordlist_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> dict:
    lstm_pipeline = REPO_ROOT / "Research" / "lstm_pipeline"
    if str(lstm_pipeline) not in sys.path:
        sys.path.insert(0, str(lstm_pipeline))

    from src.data import create_vocabulary, load_datasets  # type: ignore  # noqa: E402
    from src.utils import get_model_hyperparams_from_filename  # type: ignore  # noqa: E402

    model_path = Path(model_path or DEFAULT_MODEL).expanduser().resolve()
    train_data_dir = Path(train_data_dir or DEFAULT_TRAIN_DATA).expanduser().resolve()
    wordlist_path = Path(wordlist_path or DEFAULT_WORDLIST).expanduser().resolve()
    output_dir = Path(output_dir or DEFAULT_OUTPUT).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    params = get_model_hyperparams_from_filename(model_path.name)
    train_df, _, _ = load_datasets(str(train_data_dir))
    vocab = create_vocabulary(train_df, params["min_freq"], params["max_depth"])
    tokens = vocab.get_itos()

    model_filename = "model.pt"
    vocab_filename = "vocab.json"
    wordlist_filename = "wordlist.txt"

    shutil.copy2(model_path, output_dir / model_filename)
    shutil.copy2(wordlist_path, output_dir / wordlist_filename)

    vocab_payload = {
        "tokens": tokens,
        "default_index": 0,
        "special_tokens": {"<unk>": 0, "<sos>": 1, "<eos>": 2, "<pad>": 3},
    }
    (output_dir / vocab_filename).write_text(
        json.dumps(vocab_payload, indent=2) + "\n",
        encoding="utf-8",
    )

    manifest = {
        "id": "default",
        "name": "HunterT Default LSTM Bundle",
        "version": __version__,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "backend": "python-lstm",
        "model": {
            "backend": "python-lstm",
            "checkpoint": model_path.name,
            "source_name": model_path.name,
            "sha256": sha256_file(output_dir / model_filename),
            "max_depth": params["max_depth"],
            "min_freq": params["min_freq"],
            "embedding_size": params["embedding_size"],
            "num_layers": params["num_layers"],
            "dropout_rate": params["dropout_rate"],
            "vocab_size": len(tokens),
        },
        "files": {
            "model": model_filename,
            "vocab": vocab_filename,
            "wordlist": wordlist_filename,
        },
        "defaults": {
            "prediction_limit": 128,
            "max_depth": 3,
            "method": "GET",
            "user_agent": "HunterT/0.2.0-dev",
            "statuses": [200, 204, 301, 302, 307, 308, 401, 403],
        },
        "sources": {
            "model": str(model_path),
            "wordlist": str(wordlist_path),
            "train_data_dir": str(train_data_dir),
        },
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def export_default_bundle() -> dict:
    return export_bundle(
        model_path=DEFAULT_MODEL,
        train_data_dir=DEFAULT_TRAIN_DATA,
        wordlist_path=DEFAULT_WORDLIST,
        output_dir=DEFAULT_OUTPUT,
    )
