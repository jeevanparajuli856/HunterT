"""
Utility functions and constants.
"""

import torch
import os


def get_device():
    """Get torch device (cuda if available, else cpu)."""
    return torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def ensure_dir_exists(path):
    """Ensure directory exists, create if needed."""
    os.makedirs(path, exist_ok=True)


def get_model_hyperparams_from_filename(filename):
    """
    Extract hyperparameters from model filename.
    
    Filename format: model_MD{md}_MF{mf}_es{es}_nl{nl}_dr{dr}_loss{loss}.pt
    
    Args:
        filename (str): Model filename
        
    Returns:
        dict: Extracted hyperparameters
    """
    parts = filename.replace('.pt', '').split('_')
    
    return {
        'max_depth': int(parts[1][2:]),
        'min_freq': int(parts[2][2:]),
        'embedding_size': int(parts[3][2:]),
        'num_layers': int(parts[4][2:]),
        'dropout_rate': float(parts[5][2:]),
        'loss': float(parts[6][4:])
    }
