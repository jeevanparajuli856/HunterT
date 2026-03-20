"""
Hyperparameter grid search for LSTM model training.
Replicates grid search logic from LM_training.ipynb
"""

import os
import json
import shlex
import subprocess
import torch
from tqdm import tqdm

from .model import LSTM
from .data import load_datasets, get_dataloaders
from .training import train_model


class GridSearchTrainer:
    """
    Grid search trainer for LSTM models.
    Trains all hyperparameter combinations and saves best models.
    """
    
    def __init__(self, data_folder, saved_models_folder, device=None,
                 n_epochs=200, batch_size=128, lr=1e-3, clip=0.25,
                 early_stopping_patience=10, resume=True,
                 progress_file=None, checkpoint_dir=None,
                 sync_cmd=None, sync_every_n=1, smoke_test=False):
        """
        Initialize grid search trainer.
        
        Args:
            data_folder (str): Path to folder with train/validation/test CSVs
            saved_models_folder (str): Path to save trained models
            device: Device to train on (auto-detect if None)
            n_epochs (int): Max number of epochs per model
            batch_size (int): Batch size
            lr (float): Learning rate
            clip (float): Gradient norm clip value
            early_stopping_patience (int): Early stopping patience
        """
        self.data_folder = data_folder
        self.saved_models_folder = saved_models_folder
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        self.n_epochs = n_epochs
        self.batch_size = batch_size
        self.lr = lr
        self.clip = clip
        self.early_stopping_patience = early_stopping_patience
        self.resume = resume
        self.sync_cmd = sync_cmd
        self.sync_every_n = max(1, int(sync_every_n))
        self.smoke_test = smoke_test
        
        # Create saved_models folder
        os.makedirs(saved_models_folder, exist_ok=True)

        self.progress_file = progress_file or os.path.join(saved_models_folder, 'train_progress.json')
        self.checkpoint_dir = checkpoint_dir or os.path.join(saved_models_folder, 'checkpoints')
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        
        # Load datasets
        self.train_df, self.valid_df, self.test_df = load_datasets(data_folder)
        
        # Hyperparameter grid
        self.max_depths = [5, 10]
        self.min_freqs = [3, 5]
        self.embedding_sizes = [128, 256, 512]
        self.n_layers = [2, 3, 4]
        self.dropout_rates = [0.2, 0.4, 0.6]

        if self.smoke_test:
            self.max_depths = [self.max_depths[0]]
            self.min_freqs = [self.min_freqs[0]]
            self.embedding_sizes = [self.embedding_sizes[0]]
            self.n_layers = [self.n_layers[0]]
            self.dropout_rates = [self.dropout_rates[0]]
            self.n_epochs = min(self.n_epochs, 1)
        
        self.best_models = {}  # dict: (max_depth, min_freq) -> {'params': tuple, 'valid_loss': float, 'model_path': str}
        self.results = []  # list of training metadata
        self.completed_models = set()
        self.models_trained_since_sync = 0

        self._load_progress()

    @staticmethod
    def _combo_key(max_depth, min_freq, embedding_size, num_layers, dropout_rate):
        return (
            f"MD{max_depth}_MF{min_freq}_"
            f"es{embedding_size}_nl{num_layers}_dr{dropout_rate}"
        )

    @staticmethod
    def _global_key(max_depth, min_freq):
        return f"MD{max_depth}_MF{min_freq}"

    def _load_progress(self):
        if not self.resume or not os.path.exists(self.progress_file):
            return

        with open(self.progress_file, 'r') as f:
            progress = json.load(f)

        self.completed_models = set(progress.get('completed_models', []))
        stored_best = progress.get('best_models', {})
        for key, value in stored_best.items():
            md = value.get('max_depth')
            mf = value.get('min_freq')
            if md is None or mf is None:
                continue
            self.best_models[(md, mf)] = {
                'params': tuple(value['params']),
                'valid_loss': float(value['valid_loss']),
                'model_path': value['model_path']
            }

        print(f"Loaded progress: {len(self.completed_models)} completed model combos")

    def _save_progress(self):
        best_models_payload = {}
        for (md, mf), info in self.best_models.items():
            best_models_payload[self._global_key(md, mf)] = {
                'max_depth': md,
                'min_freq': mf,
                'params': list(info['params']),
                'valid_loss': float(info['valid_loss']),
                'model_path': info['model_path']
            }

        payload = {
            'completed_models': sorted(self.completed_models),
            'best_models': best_models_payload,
            'num_results': len(self.results)
        }

        with open(self.progress_file, 'w') as f:
            json.dump(payload, f, indent=2)

    def _maybe_sync(self, force=False):
        if not self.sync_cmd:
            return
        if not force and self.models_trained_since_sync < self.sync_every_n:
            return

        print(f"Running sync command: {self.sync_cmd}")
        completed = subprocess.run(self.sync_cmd, shell=True)
        if completed.returncode != 0:
            print("Warning: sync command failed; training will continue.")
        self.models_trained_since_sync = 0

    def _save_combo_checkpoint(self, max_depth, min_freq, embedding_size,
                               num_layers, dropout_rate, state_dict):
        filename = (
            f"combo_MD{max_depth}_MF{min_freq}_"
            f"es{embedding_size}_nl{num_layers}_dr{dropout_rate}.pt"
        )
        filepath = os.path.join(self.checkpoint_dir, filename)
        torch.save(state_dict, filepath)

    def _save_best_model_for_global(self, max_depth, min_freq, params, valid_loss, state_dict):
        embedding_size, num_layers, dropout_rate = params

        global_prefix = f"model_MD{max_depth}_MF{min_freq}_"
        for existing in os.listdir(self.saved_models_folder):
            if existing.startswith(global_prefix) and existing.endswith('.pt'):
                os.remove(os.path.join(self.saved_models_folder, existing))

        filename = (
            f"model_MD{max_depth}_MF{min_freq}_"
            f"es{embedding_size}_nl{num_layers}_dr{dropout_rate}_"
            f"loss{valid_loss:.6f}.pt"
        )
        filepath = os.path.join(self.saved_models_folder, filename)
        torch.save(state_dict, filepath)

        self.best_models[(max_depth, min_freq)] = {
            'params': params,
            'valid_loss': valid_loss,
            'model_path': filepath
        }
    
    def train_all(self):
        """
        Train all hyperparameter combinations.
        Saves best model for each (max_depth, min_freq) combination.
        """
        global_params = [
            (max_depth, min_freq)
            for max_depth in self.max_depths
            for min_freq in self.min_freqs
        ]
        
        models_per_global = len(self.embedding_sizes) * len(self.n_layers) * len(self.dropout_rates)
        print(
            f"Starting grid search: {len(global_params)} global param combos x "
            f"{models_per_global} hyperparams = {len(global_params) * models_per_global} total models"
        )
        
        for max_depth, min_freq in global_params:
            print(f"\n{'='*60}")
            print(f"Global params: MAX_DEPTH={max_depth}, MIN_FREQ={min_freq}")
            print(f"{'='*60}")
            
            # Create vocabulary and dataloaders
            vocab, train_data, valid_data = get_dataloaders(
                self.train_df, self.valid_df, min_freq, max_depth, self.batch_size
            )
            seq_len = max_depth + 2
            vocab_size = len(vocab)
            
            print(f"Vocabulary size: {vocab_size}")
            
            # Loop over hyperparameter combinations
            hyperparams = [
                (es, nl, dr)
                for es in self.embedding_sizes
                for nl in self.n_layers
                for dr in self.dropout_rates
            ]
            
            for embedding_size, num_layers, dropout_rate in hyperparams:
                combo_key = self._combo_key(max_depth, min_freq, embedding_size, num_layers, dropout_rate)
                if combo_key in self.completed_models:
                    print(f"  Skipping completed combo: {combo_key}")
                    continue

                # Train model
                print(f"  Training: es={embedding_size}, nl={num_layers}, dr={dropout_rate}")
                
                model_state_dict, valid_loss, epochs_trained = train_model(
                    LSTM,
                    vocab_size=vocab_size,
                    embedding_dim=embedding_size,
                    hidden_dim=embedding_size,  # tie_weights requires this
                    num_layers=num_layers,
                    dropout_rate=dropout_rate,
                    tie_weights=True,
                    train_data=train_data,
                    valid_data=valid_data,
                    n_epochs=self.n_epochs,
                    batch_size=self.batch_size,
                    lr=self.lr,
                    clip=self.clip,
                    early_stopping_patience=self.early_stopping_patience,
                    device=self.device,
                    seq_len=seq_len
                )
                
                # Store result
                self.results.append({
                    'max_depth': max_depth,
                    'min_freq': min_freq,
                    'embedding_size': embedding_size,
                    'num_layers': num_layers,
                    'dropout_rate': dropout_rate,
                    'valid_loss': valid_loss,
                    'epochs_trained': epochs_trained
                })

                self._save_combo_checkpoint(
                    max_depth, min_freq, embedding_size, num_layers, dropout_rate, model_state_dict
                )

                self.completed_models.add(combo_key)
                
                # Check if best for this global param combo
                best_info = self.best_models.get((max_depth, min_freq))
                if best_info is None or valid_loss < best_info['valid_loss']:
                    self._save_best_model_for_global(
                        max_depth,
                        min_freq,
                        (embedding_size, num_layers, dropout_rate),
                        valid_loss,
                        model_state_dict
                    )

                self._save_progress()
                self.models_trained_since_sync += 1
                self._maybe_sync()
            
            print(f"Best model for (MD={max_depth}, MF={min_freq}): "
                  f"es={self.best_models[(max_depth, min_freq)]['params'][0]}, "
                  f"nl={self.best_models[(max_depth, min_freq)]['params'][1]}, "
                  f"dr={self.best_models[(max_depth, min_freq)]['params'][2]}, "
                  f"loss={self.best_models[(max_depth, min_freq)]['valid_loss']:.6f}")
        
        self._save_progress()
        self._maybe_sync(force=True)
        print(f"\n{'='*60}")
        print(f"Training complete! Models saved to {self.saved_models_folder}")
        print(f"{'='*60}")
