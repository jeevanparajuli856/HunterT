"""
LSTM model definition for directory prediction.
Replicates LSTM class from LM_training.ipynb
"""

import math
import torch
import torch.nn as nn


class LSTM(nn.Module):
    """
    LSTM language model for directory prediction.
    
    Architecture:
    - Embedding layer: vocab_size → embedding_dim
    - LSTM layers: embedding_dim → hidden_dim (num_layers stacked)
    - Dropout: after embedding and after LSTM
    - FC layer: hidden_dim → vocab_size
    - Optional tied weights: embedding.weight == fc.weight
    """
    
    def __init__(self, vocab_size, embedding_dim, hidden_dim, num_layers, 
                 dropout_rate, tie_weights=True):
        """
        Initialize LSTM model.
        
        Args:
            vocab_size (int): Size of vocabulary
            embedding_dim (int): Embedding dimension
            hidden_dim (int): Hidden dimension of LSTM
            num_layers (int): Number of LSTM layers
            dropout_rate (float): Dropout probability
            tie_weights (bool): Whether to tie embedding and output weights
        """
        super().__init__()
        
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.dropout_rate = dropout_rate
        self.tie_weights = tie_weights
        
        # Embedding layer
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        
        # Dropout between embedding and LSTM
        self.emb_dropout = nn.Dropout(dropout_rate)
        
        # LSTM layer
        self.lstm = nn.LSTM(
            embedding_dim,
            hidden_dim,
            num_layers=num_layers,
            dropout=dropout_rate,
            batch_first=True
        )
        
        # Dropout between LSTM and FC
        self.lstm_dropout = nn.Dropout(dropout_rate)
        
        # Fully connected layer
        self.fc = nn.Linear(hidden_dim, vocab_size)
        
        # Tie weights if specified
        if tie_weights:
            if embedding_dim != hidden_dim:
                raise ValueError('Cannot tie weights: embedding_dim != hidden_dim')
            self.embedding.weight = self.fc.weight
        
        self.init_weights()
    
    def forward(self, src, hidden):
        """
        Forward pass.
        
        Args:
            src (torch.Tensor): Input tensor of shape (batch_size, seq_len)
            hidden (tuple): Initial hidden state (h, c) from init_hidden()
            
        Returns:
            tuple: (prediction, hidden)
                - prediction: shape (batch_size, seq_len, vocab_size)
                - hidden: updated hidden state
        """
        # Embedding
        embedding = self.emb_dropout(self.embedding(src))
        
        # LSTM
        output, hidden = self.lstm(embedding, hidden)
        
        # Dropout
        output = self.lstm_dropout(output)
        
        # FC layer
        prediction = self.fc(output)
        
        return prediction, hidden
    
    def init_weights(self):
        """Initialize model weights."""
        init_range_emb = 0.1
        init_range_other = 1 / math.sqrt(self.hidden_dim)
        
        # Embedding weights
        self.embedding.weight.data.uniform_(-init_range_emb, init_range_emb)
        
        # FC weights and bias
        self.fc.weight.data.uniform_(-init_range_other, init_range_other)
        self.fc.bias.data.zero_()
        
        # LSTM weights (stored in all_weights)
        for i in range(self.num_layers):
            self.lstm.all_weights[i][0] = torch.FloatTensor(
                self.embedding_dim, self.hidden_dim
            ).uniform_(-init_range_other, init_range_other)
            self.lstm.all_weights[i][1] = torch.FloatTensor(
                self.hidden_dim, self.hidden_dim
            ).uniform_(-init_range_other, init_range_other)
    
    def init_hidden(self, batch_size, device):
        """
        Initialize hidden state (h, c) for LSTM.
        
        Args:
            batch_size (int): Batch size
            device: Device to place tensors on
            
        Returns:
            tuple: (h, c) hidden states
        """
        h = torch.zeros(self.num_layers, batch_size, self.hidden_dim).to(device)
        c = torch.zeros(self.num_layers, batch_size, self.hidden_dim).to(device)
        return h, c
    
    def detach_hidden(self, hidden):
        """
        Detach hidden state (for truncated backprop).
        
        Args:
            hidden (tuple): (h, c) hidden states
            
        Returns:
            tuple: Detached (h, c)
        """
        h, c = hidden
        h = h.detach()
        c = c.detach()
        return h, c
