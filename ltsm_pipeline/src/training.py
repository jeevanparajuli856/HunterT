"""
Training loop with early stopping.
Replicates train(), evaluate(), and train_model() from LM_training.ipynb
"""

import copy
import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm


def train_epoch(model, data, optimizer, criterion, batch_size, seq_len, clip, device):
    """
    Train for one epoch.
    
    Args:
        model: LSTM model
        data (torch.Tensor): Training data of shape (batch_size, num_batches)
        optimizer: Adam optimizer
        criterion: CrossEntropyLoss
        batch_size (int): Batch size
        seq_len (int): Sequence length
        clip (float): Gradient norm clip value
        device: Device to train on
        
    Returns:
        float: Average epoch loss
    """
    epoch_loss = 0
    model.train()
    
    num_batches = data.shape[-1]
    data = data[:, :num_batches - (num_batches - 1) % seq_len]
    num_batches = data.shape[-1]
    
    hidden = model.init_hidden(batch_size, device)
    
    for idx in range(0, num_batches - 1, seq_len):
        optimizer.zero_grad()
        hidden = model.detach_hidden(hidden)
        
        # Get batch
        src = data[:, idx:idx + seq_len]
        target = data[:, idx + 1:idx + seq_len + 1]
        
        src, target = src.to(device), target.to(device)
        batch_size_actual = src.shape[0]
        
        # Forward pass
        prediction, hidden = model(src, hidden)
        
        # Compute loss
        prediction = prediction.reshape(batch_size_actual * seq_len, -1)
        target = target.reshape(-1)
        loss = criterion(prediction, target)
        
        # Backward pass
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
        optimizer.step()
        
        epoch_loss += loss.item() * seq_len
    
    return epoch_loss / num_batches


def evaluate_epoch(model, data, criterion, batch_size, seq_len, device):
    """
    Evaluate on validation/test set (one epoch).
    
    Args:
        model: LSTM model
        data (torch.Tensor): Validation data of shape (batch_size, num_batches)
        criterion: CrossEntropyLoss
        batch_size (int): Batch size
        seq_len (int): Sequence length
        device: Device to evaluate on
        
    Returns:
        float: Average validation loss
    """
    epoch_loss = 0
    model.eval()
    
    num_batches = data.shape[-1]
    data = data[:, :num_batches - (num_batches - 1) % seq_len]
    num_batches = data.shape[-1]
    
    hidden = model.init_hidden(batch_size, device)
    
    with torch.no_grad():
        for idx in range(0, num_batches - 1, seq_len):
            hidden = model.detach_hidden(hidden)
            
            # Get batch
            src = data[:, idx:idx + seq_len]
            target = data[:, idx + 1:idx + seq_len + 1]
            
            src, target = src.to(device), target.to(device)
            batch_size_actual = src.shape[0]
            
            # Forward pass
            prediction, hidden = model(src, hidden)
            
            # Compute loss
            prediction = prediction.reshape(batch_size_actual * seq_len, -1)
            target = target.reshape(-1)
            loss = criterion(prediction, target)
            
            epoch_loss += loss.item() * seq_len
    
    return epoch_loss / num_batches


def train_model(model_class, vocab_size, embedding_dim, hidden_dim, num_layers,
                dropout_rate, tie_weights, train_data, valid_data, n_epochs,
                batch_size, lr, clip, early_stopping_patience, device, seq_len):
    """
    Train a single model with early stopping.
    
    Args:
        model_class: LSTM class
        vocab_size (int): Vocabulary size
        embedding_dim (int): Embedding dimension
        hidden_dim (int): Hidden dimension
        num_layers (int): Number of LSTM layers
        dropout_rate (float): Dropout rate
        tie_weights (bool): Whether to tie weights
        train_data (torch.Tensor): Training data
        valid_data (torch.Tensor): Validation data
        n_epochs (int): Max number of epochs
        batch_size (int): Batch size
        lr (float): Learning rate
        clip (float): Gradient norm clip value
        early_stopping_patience (int): Early stopping patience
        device: Device to train on
        
    Returns:
        tuple: (best_model_state_dict, best_valid_loss, num_epochs_trained)
    """
    # Create model
    model = model_class(
        vocab_size, embedding_dim, hidden_dim, num_layers,
        dropout_rate, tie_weights
    ).to(device)
    
    # Optimizer and loss
    optimizer = optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss(ignore_index=3)  # ignore_index for <pad>
    
    # Learning rate scheduler
    lr_scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, factor=0.5, patience=0
    )
    
    # Early stopping
    best_valid_loss = float('inf')
    early_stopping_counter = 0
    best_model_state_dict = copy.deepcopy(model.state_dict())
    epochs_trained = 0
    
    # Training loop
    for epoch in tqdm(range(1, n_epochs + 1), desc='Training'):
        train_loss = train_epoch(model, train_data, optimizer, criterion,
                                batch_size, seq_len, clip, device)
        valid_loss = evaluate_epoch(model, valid_data, criterion,
                                   batch_size, seq_len, device)
        
        # Learning rate scheduler step
        lr_scheduler.step(valid_loss)
        
        # Track best model
        if valid_loss < best_valid_loss:
            best_valid_loss = valid_loss
            best_model_state_dict = copy.deepcopy(model.state_dict())
            early_stopping_counter = 0
        else:
            early_stopping_counter += 1
        
        # Early stopping check
        if early_stopping_counter >= early_stopping_patience:
            epochs_trained = epoch
            break
        
        epochs_trained = epoch
    
    return best_model_state_dict, best_valid_loss, epochs_trained
