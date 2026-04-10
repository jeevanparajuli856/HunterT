"""LSTM model definition used by the HunterT runtime bundle."""

from __future__ import annotations

import math

import torch
import torch.nn as nn


class LSTM(nn.Module):
    """Match the training-time LSTM architecture for bundled inference."""

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int,
        hidden_dim: int,
        num_layers: int,
        dropout_rate: float,
        tie_weights: bool = True,
    ) -> None:
        super().__init__()

        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.dropout_rate = dropout_rate
        self.tie_weights = tie_weights

        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.emb_dropout = nn.Dropout(dropout_rate)
        self.lstm = nn.LSTM(
            embedding_dim,
            hidden_dim,
            num_layers=num_layers,
            dropout=dropout_rate,
            batch_first=True,
        )
        self.lstm_dropout = nn.Dropout(dropout_rate)
        self.fc = nn.Linear(hidden_dim, vocab_size)

        if tie_weights:
            if embedding_dim != hidden_dim:
                raise ValueError("cannot tie weights when embedding_dim != hidden_dim")
            self.embedding.weight = self.fc.weight

        self._init_weights()

    def forward(self, src: torch.Tensor, hidden: tuple[torch.Tensor, torch.Tensor]):
        embedding = self.emb_dropout(self.embedding(src))
        output, hidden = self.lstm(embedding, hidden)
        output = self.lstm_dropout(output)
        prediction = self.fc(output)
        return prediction, hidden

    def init_hidden(self, batch_size: int, device: torch.device):
        h = torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=device)
        c = torch.zeros(self.num_layers, batch_size, self.hidden_dim, device=device)
        return h, c

    def _init_weights(self) -> None:
        init_range_emb = 0.1
        init_range_other = 1 / math.sqrt(self.hidden_dim)

        self.embedding.weight.data.uniform_(-init_range_emb, init_range_emb)
        self.fc.weight.data.uniform_(-init_range_other, init_range_other)
        self.fc.bias.data.zero_()

