"""
Hyperparameter grid search for LSTM model training.
Replicates grid search logic from LM_training.ipynb
"""

import os
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
                 early_stopping_patience=10):
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
        
        # Create saved_models folder
        os.makedirs(saved_models_folder, exist_ok=True)
        
        # Load datasets
        self.train_df, self.valid_df, self.test_df = load_datasets(data_folder)
        
        # Hyperparameter grid
        self.max_depths = [5, 10]
        self.min_freqs = [3, 5]
        self.embedding_sizes = [128, 256, 512]
        self.n_layers = [2, 3, 4]
        self.dropout_rates = [0.2, 0.4, 0.6]
        
        self.best_models = {}  # dict: (max_depth, min_freq) -> (params, loss, state_dict)
        self.results = []  # list of training results
    
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
        
        print(f"Starting grid search: {len(global_params)} global param combos x 27 hyperparams = 216 total models")
        
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
                    'epochs_trained': epochs_trained,
                    'model_state_dict': model_state_dict
                })
                
                # Check if best for this global param combo
                if (max_depth, min_freq) not in self.best_models or \
                   valid_loss < self.best_models[(max_depth, min_freq)][1]:
                    self.best_models[(max_depth, min_freq)] = (
                        (embedding_size, num_layers, dropout_rate),
                        valid_loss,
                        model_state_dict
                    )
            
            print(f"Best model for (MD={max_depth}, MF={min_freq}): "
                  f"es={self.best_models[(max_depth, min_freq)][0][0]}, "
                  f"nl={self.best_models[(max_depth, min_freq)][0][1]}, "
                  f"dr={self.best_models[(max_depth, min_freq)][0][2]}, "
                  f"loss={self.best_models[(max_depth, min_freq)][1]:.6f}")
        
        # Save all best models
        self._save_best_models()
        print(f"\n{'='*60}")
        print(f"Training complete! Models saved to {self.saved_models_folder}")
        print(f"{'='*60}")
    
    def _save_best_models(self):
        """Save best model for each (max_depth, min_freq) combination."""
        for (max_depth, min_freq), (params, valid_loss, state_dict) in self.best_models.items():
            embedding_size, num_layers, dropout_rate = params
            
            filename = (f"model_MD{max_depth}_MF{min_freq}_"
                       f"es{embedding_size}_nl{num_layers}_dr{dropout_rate}_"
                       f"loss{valid_loss:.6f}.pt")
            filepath = os.path.join(self.saved_models_folder, filename)
            
            torch.save(state_dict, filepath)
            print(f"Saved: {filename}")
