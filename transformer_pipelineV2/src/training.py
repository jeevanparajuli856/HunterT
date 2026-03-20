"""
Training loop for DirHunterT transformer.

V2 uses path-wise batches instead of the flat token stream used by V1.
Each training sample is one padded path, and the loss is computed on the
next-token targets inside that path only.
"""

import copy
import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm


PAD_INDEX = 3


def train_epoch(model, data_loader, optimizer, criterion, clip, device):
    """
    Train for one epoch with one padded path per sample.

    Args:
        model:          DirHunterT model
        data_loader:    DataLoader yielding tensors of shape (batch_size, seq_len)
        optimizer:      Adam with weight_decay
        criterion:      CrossEntropyLoss(ignore_index=3)
        clip (float):   Gradient norm clip value
        device:         Torch device

    Returns:
        float: Average token-level loss on non-pad targets
    """
    epoch_loss = 0.0
    token_count = 0
    model.train()

    for (batch,) in data_loader:
        optimizer.zero_grad()

        batch = batch.to(device)
        src = batch[:, :-1]
        target = batch[:, 1:]
        batch_size_actual, seq_len = src.shape

        prediction, _ = model(src, None)

        loss = criterion(
            prediction.reshape(batch_size_actual * seq_len, -1),
            target.reshape(-1),
        )
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
        optimizer.step()

        non_pad_tokens = (target != PAD_INDEX).sum().item()
        epoch_loss += loss.item() * non_pad_tokens
        token_count += non_pad_tokens

    return epoch_loss / max(token_count, 1)


def evaluate_epoch(model, data_loader, criterion, device):
    """
    Evaluate on validation set.

    Args:
        model:          DirHunterT model
        data_loader:    DataLoader yielding tensors of shape (batch_size, seq_len)
        criterion:      CrossEntropyLoss
        device:         Torch device

    Returns:
        float: Average token-level loss on non-pad targets
    """
    epoch_loss = 0.0
    token_count = 0
    model.eval()

    with torch.no_grad():
        for (batch,) in data_loader:
            batch = batch.to(device)
            src = batch[:, :-1]
            target = batch[:, 1:]
            batch_size_actual, seq_len = src.shape

            prediction, _ = model(src, None)

            loss = criterion(
                prediction.reshape(batch_size_actual * seq_len, -1),
                target.reshape(-1),
            )
            non_pad_tokens = (target != PAD_INDEX).sum().item()
            epoch_loss += loss.item() * non_pad_tokens
            token_count += non_pad_tokens

    return epoch_loss / max(token_count, 1)


def train_model(model_class, vocab_size, d_model, n_heads, n_layers, dropout,
                max_depth, vocab, train_loader, valid_loader, n_epochs,
                lr, clip, early_stopping_patience, device,
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
        train_loader:             Training DataLoader with one padded path per sample
        valid_loader:             Validation DataLoader with one padded path per sample
        n_epochs (int):           Max epochs
        lr (float):               Peak learning rate
        clip (float):             Gradient norm clip value
        early_stopping_patience:  Stop if no improvement for this many epochs
        device:                   Torch device
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
    criterion = nn.CrossEntropyLoss(ignore_index=PAD_INDEX)

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
            model, train_loader, optimizer, criterion, clip, device
        )
        valid_loss = evaluate_epoch(
            model, valid_loader, criterion, device
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
