"""
Path-wise data loading utilities for the fair transformer comparison.

Unlike the original flat tensor loader, this module keeps each padded path as an
independent training example so the transformer sees clean per-path positions.
"""

import torch
from torch.utils.data import DataLoader, TensorDataset

from lstm_pipeline.src.data import create_vocabulary, custom_tokenizer


def _encode_paths(paths, vocab, max_depth):
    """
    Encode raw paths into a fixed-shape tensor of padded token ids.

    Each row is:
      <sos> tok_1 ... tok_n <eos> <pad> ...

    The output shape is (num_paths, max_depth + 2).
    """
    seq_len = max_depth + 2
    encoded = []

    for path in paths:
        token_list = ['<sos>'] + custom_tokenizer(path, max_depth) + ['<eos>']
        token_list = token_list[:seq_len]

        if len(token_list) < seq_len:
            token_list = token_list + ['<pad>'] * (seq_len - len(token_list))

        encoded.append([vocab[token] for token in token_list])

    return torch.LongTensor(encoded)


def get_path_dataloaders(train_df, validation_df, min_freq, max_depth, batch_size):
    """
    Build fair per-path dataloaders for transformer training.

    Returns:
        tuple: (vocab, train_loader, valid_loader)
    """
    vocab = create_vocabulary(train_df, min_freq, max_depth)

    train_tensor = _encode_paths(train_df['Path'], vocab, max_depth)
    valid_tensor = _encode_paths(validation_df['Path'], vocab, max_depth)

    train_loader = DataLoader(
        TensorDataset(train_tensor),
        batch_size=batch_size,
        shuffle=True,
        drop_last=False,
    )
    valid_loader = DataLoader(
        TensorDataset(valid_tensor),
        batch_size=batch_size,
        shuffle=False,
        drop_last=False,
    )

    return vocab, train_loader, valid_loader
