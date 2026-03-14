"""
DirHunterT: Decoder-only transformer for directory prediction.

Architecture improvements over LSTM:
  1. Full causal attention   — lossless path context (vs LSTM's lossy hidden state)
  2. Depth-aware positional  — learnable depth embeddings (depth matters more than sequence order)
  3. Segment-type embeddings — structural category of each directory token (8 types)
  4. Pre-Layer Norm          — more stable gradients on small datasets

Interface is drop-in compatible with LSTM:
  forward(src, hidden) -> (prediction, hidden)
  init_hidden(batch_size, device) -> None
  detach_hidden(hidden) -> None
"""

import math
import torch
import torch.nn as nn


# ---------------------------------------------------------------------------
# Segment type keyword mapping
# Each token string is mapped to one of 8 structural category indices.
# Lookup happens at init time — stored as a buffer with the model weights.
# ---------------------------------------------------------------------------

# Map: segment_type_idx -> set of lowercase keyword strings
_SEGMENT_KEYWORDS: dict[int, set] = {
    0: {  # API / versioned endpoints
        'api', 'v1', 'v2', 'v3', 'v4', 'v5', 'rest', 'graphql',
        'webhook', 'webhooks', 'rpc', 'grpc', 'endpoint', 'endpoints',
    },
    1: {  # Admin / Auth / User management
        'admin', 'login', 'logout', 'auth', 'authenticate', 'authorization',
        'dashboard', 'user', 'users', 'account', 'accounts', 'password',
        'register', 'signin', 'signup', 'profile', 'profiles', 'settings',
        'session', 'token', 'oauth', 'sso',
    },
    2: {  # Content / Publishing
        'news', 'blog', 'blogs', 'article', 'articles', 'post', 'posts',
        'press', 'content', 'media', 'story', 'stories', 'publications',
        'publication', 'announcement', 'announcements', 'release', 'releases',
        'press-release', 'press-releases', 'spotlight',
    },
    3: {  # Static assets
        'static', 'assets', 'img', 'images', 'image', 'css', 'js',
        'javascript', 'fonts', 'font', 'files', 'uploads', 'upload',
        'icons', 'icon', 'logo', 'logos', 'themes', 'theme',
    },
    4: {  # Data / Operations
        'data', 'export', 'exports', 'report', 'reports', 'upload', 'uploads',
        'search', 'feed', 'feeds', 'import', 'imports', 'results',
        'analytics', 'stats', 'statistics', 'metrics',
    },
    5: {  # Organizational / Informational
        'about', 'about-us', 'contact', 'careers', 'jobs', 'team', 'staff',
        'services', 'help', 'support', 'faq', 'terms', 'privacy',
        'locations', 'location', 'departments', 'department', 'faculty',
        'research', 'programs', 'program', 'resources', 'resource',
        'alumni', 'visitors', 'directory',
    },
    6: {  # Temporal (YEAR token + date-related)
        'year', 'archive', 'archives', 'history',
    },
    # Type 7 = default / unknown (all other tokens including special tokens)
}

# Flat reverse map: token_string -> segment_type_idx (built once at module load)
_TOKEN_TO_SEGMENT: dict[str, int] = {}
for _seg_type, _keywords in _SEGMENT_KEYWORDS.items():
    for _kw in _keywords:
        _TOKEN_TO_SEGMENT[_kw] = _seg_type


def _build_segment_buffer(vocab_size: int, vocab) -> torch.Tensor:
    """
    Build a (vocab_size,) LongTensor mapping token index -> segment type index.
    Type 7 is the default for all unrecognized tokens (including special tokens).
    """
    buf = torch.full((vocab_size,), 7, dtype=torch.long)
    if vocab is None:
        return buf
    itos = vocab.get_itos()
    for idx, token in enumerate(itos):
        seg = _TOKEN_TO_SEGMENT.get(token.lower(), 7)
        buf[idx] = seg
    return buf


# ---------------------------------------------------------------------------
# DirHunterT model
# ---------------------------------------------------------------------------

class DirHunterT(nn.Module):
    """
    Decoder-only transformer language model for directory path prediction.

    Drop-in compatible with the LSTM attack loop:
      forward(src, hidden) -> (logits, None)
      init_hidden(batch_size, device) -> None
      detach_hidden(hidden) -> None

    Args:
        vocab_size  (int):   Vocabulary size (same as LSTM)
        d_model     (int):   Transformer hidden dimension (replaces embedding_dim + hidden_dim)
        n_heads     (int):   Number of attention heads (must divide d_model)
        n_layers    (int):   Number of transformer encoder layers
        dropout     (float): Dropout rate applied to embeddings and attention
        max_depth   (int):   Max path depth used during training (controls depth embedding size)
        vocab:               torchtext vocab object — used to build segment type buffer.
                             If None, all tokens default to segment type 7 (Other).
        n_segment_types (int): Number of structural segment categories (default: 8)
    """

    def __init__(self, vocab_size: int, d_model: int, n_heads: int, n_layers: int,
                 dropout: float, max_depth: int, vocab=None, n_segment_types: int = 8):
        super().__init__()

        assert d_model % n_heads == 0, (
            f"d_model ({d_model}) must be divisible by n_heads ({n_heads})"
        )

        self.vocab_size = vocab_size
        self.d_model = d_model
        self.n_heads = n_heads
        self.n_layers = n_layers
        self.dropout_rate = dropout
        self.max_depth = max_depth
        self.n_segment_types = n_segment_types

        # --- Three additive input representations ---

        # 1. Token embedding: standard lookup, padding_idx=3 so <pad> gets zero gradient
        self.token_embedding = nn.Embedding(vocab_size, d_model, padding_idx=3)

        # 2. Depth-aware positional embedding: learnable, one vector per depth level.
        #    Position 0 = <sos>, position 1 = first directory, etc.
        #    max_depth + 2 covers <sos> (0) + max_depth tokens + <eos>
        self.depth_embedding = nn.Embedding(max_depth + 2, d_model)

        # 3. Segment-type embedding: structural category of each directory token
        self.segment_embedding = nn.Embedding(n_segment_types, d_model)

        self.emb_dropout = nn.Dropout(dropout)

        # --- Transformer encoder used as causal (decoder-only) model ---
        # norm_first=True = Pre-Layer Norm: more stable gradients on small datasets
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True,
            norm_first=True,          # Pre-LN: better stability than Post-LN
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=n_layers,
            enable_nested_tensor=False,   # avoid shape issues with padding masks
        )

        # Output projection: d_model -> vocab_size
        self.fc = nn.Linear(d_model, vocab_size)

        # Segment type buffer: maps token index -> segment type index (saved with model)
        self.register_buffer('segment_type_buffer', _build_segment_buffer(vocab_size, vocab))

        self._init_weights()

    # ------------------------------------------------------------------
    # Weight initialisation
    # ------------------------------------------------------------------

    def _init_weights(self):
        """Xavier uniform for projection layers; small uniform for embeddings."""
        init_range = 0.1
        self.token_embedding.weight.data.uniform_(-init_range, init_range)
        self.depth_embedding.weight.data.uniform_(-init_range, init_range)
        self.segment_embedding.weight.data.uniform_(-init_range, init_range)

        nn.init.xavier_uniform_(self.fc.weight)
        nn.init.zeros_(self.fc.bias)

        for layer in self.transformer.layers:
            for p in layer.parameters():
                if p.dim() > 1:
                    nn.init.xavier_uniform_(p)

    # ------------------------------------------------------------------
    # Forward pass
    # ------------------------------------------------------------------

    def forward(self, src: torch.Tensor, hidden=None):
        """
        Forward pass (causal/autoregressive).

        Args:
            src    (torch.Tensor): Token indices, shape (batch_size, seq_len)
            hidden: Ignored — present only for LSTM interface compatibility.

        Returns:
            tuple: (logits, None)
                logits shape: (batch_size, seq_len, vocab_size)
                None replaces the LSTM hidden state (transformer is stateless)
        """
        batch_size, seq_len = src.shape

        # Clamp depth positions to max_depth+1 to avoid OOB on longer sequences
        positions = torch.arange(seq_len, device=src.device).unsqueeze(0)  # (1, seq_len)
        positions = positions.clamp(max=self.max_depth + 1)

        # Segment types from pre-built buffer (fast integer lookup)
        seg_types = self.segment_type_buffer[src]                           # (batch, seq_len)

        # Additive embedding combination
        x = (
            self.token_embedding(src)
            + self.depth_embedding(positions.expand(batch_size, -1))
            + self.segment_embedding(seg_types)
        )
        x = self.emb_dropout(x)

        # Padding mask (bool): True = PAD token, will be ignored in attention
        pad_mask = (src == 3)                                               # (batch, seq_len)

        # Causal mask (bool): True = blocked position (upper triangle = future tokens).
        # Using bool for both masks eliminates PyTorch mixed-type deprecation warnings.
        causal_mask = torch.ones(
            seq_len, seq_len, dtype=torch.bool, device=src.device
        ).triu(diagonal=1)

        x = self.transformer(x, mask=causal_mask, src_key_padding_mask=pad_mask)

        logits = self.fc(x)                                                 # (batch, seq_len, vocab_size)
        return logits, None

    # ------------------------------------------------------------------
    # LSTM-compatible state management (stubs — transformer is stateless)
    # ------------------------------------------------------------------

    def init_hidden(self, batch_size: int, device):
        """Return None — transformer has no recurrent state."""
        return None

    def detach_hidden(self, hidden):
        """Return None — no hidden state to detach."""
        return None
