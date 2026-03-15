"""
Training loop for DirHunterT transformer.

Adapted from ltsm_pipeline/src/training.py.
Key differences from the LSTM version:
  - No hidden state management (no init_hidden / detach_hidden calls)
  - Weight decay added to Adam (prevents overfitting on 1M-scale data)
  - Warmup scheduler: linear warmup for first `warmup_epochs` epochs,
    then ReduceLROnPlateau as before
  - model_class constructor takes (vocab_size, d_model, n_heads, n_layers,
    dropout, max_depth, vocab) — different from LSTM signature
"""

import copy
import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm


def train_epoch(model, data, optimizer, criterion, batch_size, seq_len, clip, device):
    """
    Train for one epoch using the same chunked iteration as the LSTM.

    Each seq_len chunk corresponds to one complete padded path sequence
    (get_dataloaders pads every path to exactly seq_len = max_depth + 2).

    Args:
        model:          DirHunterT model
        data (Tensor):  Shape (batch_size, total_tokens)
        optimizer:      Adam with weight_decay
        criterion:      CrossEntropyLoss(ignore_index=3)
        batch_size (int): Batch size
        seq_len (int):  Sequence length (max_depth + 2)
        clip (float):   Gradient norm clip value
        device:         Torch device

    Returns:
        float: Average epoch loss
    """
    epoch_loss = 0
    model.train()

    num_batches = data.shape[-1]
    data = data[:, :num_batches - (num_batches - 1) % seq_len]
    num_batches = data.shape[-1]

    for idx in range(0, num_batches - 1, seq_len):
        optimizer.zero_grad()

        src    = data[:, idx     : idx + seq_len    ].to(device)
        target = data[:, idx + 1 : idx + seq_len + 1].to(device)
        batch_size_actual = src.shape[0]

        prediction, _ = model(src, None)

        loss = criterion(
            prediction.reshape(batch_size_actual * seq_len, -1),
            target.reshape(-1),
        )
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
        optimizer.step()

        epoch_loss += loss.item() * seq_len

    return epoch_loss / num_batches


def evaluate_epoch(model, data, criterion, batch_size, seq_len, device):
    """
    Evaluate on validation set.

    Args:
        model:          DirHunterT model
        data (Tensor):  Shape (batch_size, total_tokens)
        criterion:      CrossEntropyLoss
        batch_size (int): Batch size
        seq_len (int):  Sequence length
        device:         Torch device

    Returns:
        float: Average validation loss
    """
    epoch_loss = 0
    model.eval()

    num_batches = data.shape[-1]
    data = data[:, :num_batches - (num_batches - 1) % seq_len]
    num_batches = data.shape[-1]

    with torch.no_grad():
        for idx in range(0, num_batches - 1, seq_len):
            src    = data[:, idx     : idx + seq_len    ].to(device)
            target = data[:, idx + 1 : idx + seq_len + 1].to(device)
            batch_size_actual = src.shape[0]

            prediction, _ = model(src, None)

            loss = criterion(
                prediction.reshape(batch_size_actual * seq_len, -1),
                target.reshape(-1),
            )
            epoch_loss += loss.item() * seq_len

    return epoch_loss / num_batches


def train_model(model_class, vocab_size, d_model, n_heads, n_layers, dropout,
                max_depth, vocab, train_data, valid_data, n_epochs,
                batch_size, lr, clip, early_stopping_patience, device, seq_len,
                weight_decay=1e-4, warmup_epochs=5, disable_segment_emb=False):
    """
    Train a single DirHunterT model with early stopping.

    Args:
        model_class:              DirHunterT class
        vocab_size (int):         Vocabulary size
        d_model (int):            Transformer hidden dimension
        n_heads (int):            Number of attention heads
        n_layers (int):           Number of transformer layers
        dropout (float):          Dropout rate
        max_depth (int):          Max path depth (controls depth embedding size)
        vocab:                    torchtext vocab (for segment type buffer)
        train_data (Tensor):      Training data (batch_size, total_tokens)
        valid_data (Tensor):      Validation data
        n_epochs (int):           Max epochs
        batch_size (int):         Batch size
        lr (float):               Peak learning rate
        clip (float):             Gradient norm clip value
        early_stopping_patience:  Stop if no improvement for this many epochs
        device:                   Torch device
        seq_len (int):            Sequence length (max_depth + 2)
        weight_decay (float):     L2 regularisation — important for transformers (default 1e-4)
        warmup_epochs (int):      Linear LR warmup duration (default 5 epochs)

    Returns:
        tuple: (best_state_dict, best_valid_loss, epochs_trained)
    """
    model = model_class(
        vocab_size=vocab_size,
        d_model=d_model,
        n_heads=n_heads,
        n_layers=n_layers,
        dropout=dropout,
        max_depth=max_depth,
        vocab=vocab,
        disable_segment_emb=disable_segment_emb,
    ).to(device)

    # Adam with weight decay — key difference from LSTM training
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    criterion = nn.CrossEntropyLoss(ignore_index=3)   # ignore <pad> token index 3

    # Linear warmup for first warmup_epochs, then ReduceLROnPlateau takes over
    def _warmup_lambda(epoch):
        if epoch < warmup_epochs:
            return (epoch + 1) / warmup_epochs
        return 1.0

    warmup_scheduler = optim.lr_scheduler.LambdaLR(optimizer, lr_lambda=_warmup_lambda)
    plateau_scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, factor=0.5, patience=0
    )

    best_valid_loss = float('inf')
    early_stopping_counter = 0
    best_state_dict = copy.deepcopy(model.state_dict())
    epochs_trained = 0

    for epoch in tqdm(range(1, n_epochs + 1), desc='Training'):
        train_loss = train_epoch(
            model, train_data, optimizer, criterion, batch_size, seq_len, clip, device
        )
        valid_loss = evaluate_epoch(
            model, valid_data, criterion, batch_size, seq_len, device
        )

        # Warmup scheduler steps every epoch regardless
        warmup_scheduler.step()

        # Plateau scheduler only activates after warmup
        if epoch >= warmup_epochs:
            plateau_scheduler.step(valid_loss)

        if valid_loss < best_valid_loss:
            best_valid_loss = valid_loss
            best_state_dict = copy.deepcopy(model.state_dict())
            early_stopping_counter = 0
        else:
            early_stopping_counter += 1

        if early_stopping_counter >= early_stopping_patience:
            epochs_trained = epoch
            break

        epochs_trained = epoch

    return best_state_dict, best_valid_loss, epochs_trained
