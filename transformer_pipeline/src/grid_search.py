"""
Hyperparameter grid search for DirHunterT transformer training.

Grid dimensions:
  Global  (same as LSTM for fair comparison): max_depth=[5,10], min_freq=[3,5]
  Architecture: d_model=[128,256,512], n_heads=[4,8], n_layers=[4,6], dropout=[0.2,0.4,0.6]
  Total: 4 global × 24 arch = 96 combinations (vs LSTM's 108)

d_model=128 added: may outperform larger models on small vocabs (~100 tokens).
dropout=0.6 added: LSTM's best models sometimes used high regularisation.

Best model per (max_depth, min_freq) global pair is saved — produces 4 final
models matching the 4 LSTM models for direct comparison.

Spot VM safety features (identical to LSTM pipeline):
  - Resume: skip already-completed combos via progress JSON
  - Checkpoints: per-combo .pt saved to checkpoint_dir
  - GCS sync: optional sync_cmd run every sync_every_n combos
"""

import os
import json
import subprocess
import torch
from tqdm import tqdm

from .model import DirHunterT
from .training import train_model

import sys
_ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from ltsm_pipeline.src.data import load_datasets, get_dataloaders


class TransformerGridSearch:
    """
    Grid search trainer for DirHunterT transformer models.
    API mirrors ltsm_pipeline GridSearchTrainer for easy switching.
    """

    def __init__(self, data_folder, saved_models_folder, device=None,
                 n_epochs=200, batch_size=128, lr=1e-3, clip=0.25,
                 early_stopping_patience=10, weight_decay=1e-4, warmup_epochs=5,
                 resume=True, progress_file=None, checkpoint_dir=None,
                 sync_cmd=None, sync_every_n=1, smoke_test=False):
        """
        Args:
            data_folder (str):            Path to LM-training-datasets folder
            saved_models_folder (str):    Path to save best models
            device:                       Auto-detect if None
            n_epochs (int):               Max epochs per combo
            batch_size (int):             Batch size
            lr (float):                   Peak learning rate
            clip (float):                 Gradient norm clip
            early_stopping_patience (int):Early stopping patience
            weight_decay (float):         Adam L2 regularisation (default 1e-4)
            warmup_epochs (int):          Linear LR warmup epochs (default 5)
            resume (bool):                Skip completed combos if True
            progress_file (str):          Path to JSON progress tracker
            checkpoint_dir (str):         Per-combo checkpoint directory
            sync_cmd (str):               Shell command for GCS sync (optional)
            sync_every_n (int):           Sync every N completed combos
            smoke_test (bool):            Run 1 model, 1 epoch only
        """
        self.data_folder = data_folder
        self.saved_models_folder = saved_models_folder
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.n_epochs = n_epochs
        self.batch_size = batch_size
        self.lr = lr
        self.clip = clip
        self.early_stopping_patience = early_stopping_patience
        self.weight_decay = weight_decay
        self.warmup_epochs = warmup_epochs
        self.resume = resume
        self.sync_cmd = sync_cmd
        self.sync_every_n = max(1, int(sync_every_n))
        self.smoke_test = smoke_test

        os.makedirs(saved_models_folder, exist_ok=True)

        self.progress_file = progress_file or os.path.join(saved_models_folder, 'train_progress.json')
        self.checkpoint_dir = checkpoint_dir or os.path.join(saved_models_folder, 'checkpoints')
        os.makedirs(self.checkpoint_dir, exist_ok=True)

        self.train_df, self.valid_df, self.test_df = load_datasets(data_folder)

        # ---- Hyperparameter grid ----
        # Global params match LSTM exactly (mandatory for fair A/B comparison)
        self.max_depths    = [5, 10]
        self.min_freqs     = [3, 5]
        # Transformer architecture params
        # d_model=128: often optimal for small vocabs (~100 tokens); low compute cost
        # dropout=0.6: matches high-regularisation LSTM configs that performed well
        self.d_models      = [128, 256, 512]
        self.n_heads_list  = [4, 8]
        self.n_layers_list = [4, 6]
        self.dropout_rates = [0.2, 0.4, 0.6]

        if self.smoke_test:
            self.max_depths    = [self.max_depths[0]]
            self.min_freqs     = [self.min_freqs[0]]
            self.d_models      = [self.d_models[0]]
            self.n_heads_list  = [self.n_heads_list[0]]
            self.n_layers_list = [self.n_layers_list[0]]
            self.dropout_rates = [self.dropout_rates[0]]
            self.n_epochs      = min(self.n_epochs, 1)

        self.best_models = {}        # (max_depth, min_freq) -> info dict
        self.results = []
        self.completed_models = set()
        self.models_trained_since_sync = 0

        self._load_progress()

    # ------------------------------------------------------------------
    # Key generation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _combo_key(max_depth, min_freq, d_model, n_heads, n_layers, dropout):
        return (
            f"MD{max_depth}_MF{min_freq}_"
            f"dm{d_model}_nh{n_heads}_nl{n_layers}_dr{dropout}"
        )

    @staticmethod
    def _global_key(max_depth, min_freq):
        return f"MD{max_depth}_MF{min_freq}"

    # ------------------------------------------------------------------
    # Progress persistence
    # ------------------------------------------------------------------

    def _load_progress(self):
        if not self.resume or not os.path.exists(self.progress_file):
            return
        with open(self.progress_file) as f:
            progress = json.load(f)
        self.completed_models = set(progress.get('completed_models', []))
        for key, value in progress.get('best_models', {}).items():
            md = value.get('max_depth')
            mf = value.get('min_freq')
            if md is None or mf is None:
                continue
            self.best_models[(md, mf)] = {
                'params':     tuple(value['params']),
                'valid_loss': float(value['valid_loss']),
                'model_path': value['model_path'],
            }
        print(f"Loaded progress: {len(self.completed_models)} completed combos")

    def _save_progress(self):
        best_payload = {}
        for (md, mf), info in self.best_models.items():
            best_payload[self._global_key(md, mf)] = {
                'max_depth':  md,
                'min_freq':   mf,
                'params':     list(info['params']),
                'valid_loss': float(info['valid_loss']),
                'model_path': info['model_path'],
            }
        payload = {
            'completed_models': sorted(self.completed_models),
            'best_models':      best_payload,
            'num_results':      len(self.results),
        }
        with open(self.progress_file, 'w') as f:
            json.dump(payload, f, indent=2)

    def _maybe_sync(self, force=False):
        if not self.sync_cmd:
            return
        if not force and self.models_trained_since_sync < self.sync_every_n:
            return
        print(f"Running sync: {self.sync_cmd}")
        completed = subprocess.run(self.sync_cmd, shell=True)
        if completed.returncode != 0:
            print("Warning: sync command failed; training continues.")
        self.models_trained_since_sync = 0

    def _save_combo_checkpoint(self, max_depth, min_freq, d_model, n_heads,
                                n_layers, dropout, state_dict):
        filename = (
            f"combo_MD{max_depth}_MF{min_freq}_"
            f"dm{d_model}_nh{n_heads}_nl{n_layers}_dr{dropout}.pt"
        )
        torch.save(state_dict, os.path.join(self.checkpoint_dir, filename))

    def _save_best_model_for_global(self, max_depth, min_freq, params,
                                     valid_loss, state_dict):
        d_model, n_heads, n_layers, dropout = params

        prefix = f"model_MD{max_depth}_MF{min_freq}_"
        for existing in os.listdir(self.saved_models_folder):
            if existing.startswith(prefix) and existing.endswith('.pt'):
                os.remove(os.path.join(self.saved_models_folder, existing))

        filename = (
            f"model_MD{max_depth}_MF{min_freq}_"
            f"dm{d_model}_nh{n_heads}_nl{n_layers}_dr{dropout}_"
            f"loss{valid_loss:.6f}.pt"
        )
        filepath = os.path.join(self.saved_models_folder, filename)
        torch.save(state_dict, filepath)

        self.best_models[(max_depth, min_freq)] = {
            'params':     params,
            'valid_loss': valid_loss,
            'model_path': filepath,
        }

    # ------------------------------------------------------------------
    # Main training loop
    # ------------------------------------------------------------------

    def train_all(self):
        """Train all 96 hyperparameter combinations."""
        global_params = [
            (md, mf)
            for md in self.max_depths
            for mf in self.min_freqs
        ]
        arch_params = [
            (dm, nh, nl, dr)
            for dm in self.d_models
            for nh in self.n_heads_list
            for nl in self.n_layers_list
            for dr in self.dropout_rates
        ]

        total = len(global_params) * len(arch_params)
        print(
            f"\nDirHunterT grid search: {len(global_params)} global × "
            f"{len(arch_params)} arch = {total} total models"
        )

        for max_depth, min_freq in global_params:
            print(f"\n{'='*60}")
            print(f"Global params: MAX_DEPTH={max_depth}, MIN_FREQ={min_freq}")
            print(f"{'='*60}")

            vocab, train_data, valid_data = get_dataloaders(
                self.train_df, self.valid_df, min_freq, max_depth, self.batch_size
            )
            seq_len = max_depth + 2
            vocab_size = len(vocab)
            print(f"Vocabulary size: {vocab_size}  |  seq_len: {seq_len}")

            for d_model, n_heads, n_layers, dropout in arch_params:
                combo_key = self._combo_key(
                    max_depth, min_freq, d_model, n_heads, n_layers, dropout
                )
                if combo_key in self.completed_models:
                    print(f"  Skipping completed: {combo_key}")
                    continue

                print(
                    f"  Training: d_model={d_model}, n_heads={n_heads}, "
                    f"n_layers={n_layers}, dropout={dropout}"
                )

                # Disable segment embeddings when vocab is large: keyword lists cover
                # <5% of tokens, making the type-7 embedding a near-constant noise term.
                disable_seg = vocab_size > 5000

                state_dict, valid_loss, epochs_trained = train_model(
                    model_class=DirHunterT,
                    vocab_size=vocab_size,
                    d_model=d_model,
                    n_heads=n_heads,
                    n_layers=n_layers,
                    dropout=dropout,
                    max_depth=max_depth,
                    vocab=vocab,
                    disable_segment_emb=disable_seg,
                    train_data=train_data,
                    valid_data=valid_data,
                    n_epochs=self.n_epochs,
                    batch_size=self.batch_size,
                    lr=self.lr,
                    clip=self.clip,
                    early_stopping_patience=self.early_stopping_patience,
                    device=self.device,
                    seq_len=seq_len,
                    weight_decay=self.weight_decay,
                    warmup_epochs=self.warmup_epochs,
                )

                print(f"    -> valid_loss={valid_loss:.6f}  epochs={epochs_trained}")

                self.results.append({
                    'max_depth': max_depth, 'min_freq': min_freq,
                    'd_model': d_model, 'n_heads': n_heads,
                    'n_layers': n_layers, 'dropout': dropout,
                    'valid_loss': valid_loss, 'epochs_trained': epochs_trained,
                })

                self._save_combo_checkpoint(
                    max_depth, min_freq, d_model, n_heads, n_layers, dropout, state_dict
                )
                self.completed_models.add(combo_key)

                best_info = self.best_models.get((max_depth, min_freq))
                if best_info is None or valid_loss < best_info['valid_loss']:
                    self._save_best_model_for_global(
                        max_depth, min_freq,
                        (d_model, n_heads, n_layers, dropout),
                        valid_loss, state_dict,
                    )

                self._save_progress()
                self.models_trained_since_sync += 1
                self._maybe_sync()

            info = self.best_models.get((max_depth, min_freq))
            if info:
                dm, nh, nl, dr = info['params']
                print(
                    f"Best (MD={max_depth}, MF={min_freq}): "
                    f"d_model={dm}, n_heads={nh}, n_layers={nl}, dropout={dr}, "
                    f"loss={info['valid_loss']:.6f}"
                )

        self._save_progress()
        self._maybe_sync(force=True)
        print(f"\n{'='*60}")
        print(f"Grid search complete. Models saved to {self.saved_models_folder}")
        print(f"{'='*60}")
