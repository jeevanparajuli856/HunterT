"""
Utility functions for the transformer pipeline.
"""

import torch
import os
import re


def get_device():
    """Get torch device (cuda if available, else cpu)."""
    return torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def get_transformer_hyperparams_from_filename(filename: str) -> dict:
    """
    Extract transformer hyperparameters from model filename.

    Filename format:
        model_MD{md}_MF{mf}_dm{dm}_nh{nh}_nl{nl}_dr{dr}_loss{loss}.pt

    Example:
        model_MD10_MF3_dm256_nh8_nl4_dr0.2_loss3.456789.pt

    Returns:
        dict with keys: max_depth, min_freq, d_model, n_heads, n_layers,
                        dropout_rate, loss
    """
    name = os.path.basename(filename).replace('.pt', '')
    parts = name.split('_')

    # Expected parts: ['model', 'MD{x}', 'MF{x}', 'dm{x}', 'nh{x}', 'nl{x}', 'dr{x}', 'loss{x}']
    try:
        return {
            'max_depth':    int(parts[1][2:]),
            'min_freq':     int(parts[2][2:]),
            'd_model':      int(parts[3][2:]),
            'n_heads':      int(parts[4][2:]),
            'n_layers':     int(parts[5][2:]),
            'dropout_rate': float(parts[6][2:]),
            'loss':         float(parts[7][4:]),
        }
    except (IndexError, ValueError) as e:
        raise ValueError(
            f"Cannot parse transformer hyperparams from filename '{filename}'. "
            f"Expected format: model_MD{{md}}_MF{{mf}}_dm{{dm}}_nh{{nh}}_nl{{nl}}_dr{{dr}}_loss{{loss}}.pt"
        ) from e
