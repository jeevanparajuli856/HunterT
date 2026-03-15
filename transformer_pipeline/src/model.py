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
        'api', 'apis', 'v1', 'v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8', 'v9', 'v10',
        'rest', 'restful', 'graphql', 'gql', 'webhook', 'webhooks', 'rpc', 'grpc',
        'endpoint', 'endpoints', 'service', 'services', 'gateway', 'proxy',
        'swagger', 'openapi', 'schema', 'schemas', 'wsdl', 'soap',
        'mobile', 'app', 'apps', 'public', 'internal', 'external', 'integration',
    },
    1: {  # Admin / Auth / User management
        'admin', 'administration', 'administrator', 'administrador', 'manage', 'management',
        'login', 'logout', 'logon', 'logoff', 'auth', 'authenticate', 'authentication',
        'authorization', 'authorize', 'dashboard', 'panel', 'control', 'console',
        'user', 'users', 'account', 'accounts', 'password', 'passwords', 'passwd',
        'register', 'registration', 'signin', 'signup', 'sign-in', 'sign-up',
        'profile', 'profiles', 'settings', 'preferences', 'config', 'configuration',
        'session', 'sessions', 'token', 'tokens', 'oauth', 'sso', 'saml', 'ldap',
        'member', 'members', 'membership', 'subscriber', 'subscribers', 'subscription',
        'role', 'roles', 'permission', 'permissions', 'access', 'acl', 'security',
        'wp-admin', 'wp-login', 'wp-content', 'cms', 'backend', 'staff-admin',
        'myaccount', 'my-account', 'portal', 'secure', 'private',
    },
    2: {  # Content / Publishing
        'news', 'blog', 'blogs', 'blogging', 'article', 'articles', 'post', 'posts',
        'press', 'content', 'contents', 'media', 'story', 'stories', 'publications',
        'publication', 'announcement', 'announcements', 'release', 'releases',
        'press-release', 'press-releases', 'spotlight', 'editorial', 'magazine',
        'journal', 'journals', 'newsletter', 'newsletters', 'digest', 'podcast',
        'video', 'videos', 'audio', 'gallery', 'galleries', 'photo', 'photos',
        'event', 'events', 'calendar', 'seminar', 'seminars', 'webinar', 'webinars',
        'conference', 'conferences', 'workshop', 'workshops', 'training', 'course',
        'courses', 'tutorial', 'tutorials', 'lesson', 'lessons', 'lecture', 'lectures',
        'page', 'pages', 'category', 'categories', 'tag', 'tags', 'topic', 'topics',
    },
    3: {  # Static assets
        'static', 'assets', 'asset', 'img', 'images', 'image', 'css', 'js', 'jsx',
        'javascript', 'typescript', 'ts', 'fonts', 'font', 'files', 'uploads', 'upload',
        'icons', 'icon', 'logo', 'logos', 'themes', 'theme', 'dist', 'build', 'bundle',
        'public', 'media', 'cdn', 'lib', 'libs', 'vendor', 'vendors', 'node_modules',
        'scripts', 'script', 'styles', 'style', 'stylesheets', 'downloads', 'download',
        'attachments', 'attachment', 'resources', 'resource', 'res',
    },
    4: {  # Data / Operations
        'data', 'database', 'db', 'export', 'exports', 'report', 'reports', 'reporting',
        'upload', 'uploads', 'search', 'query', 'feed', 'feeds', 'rss', 'atom',
        'import', 'imports', 'results', 'result', 'analytics', 'stats', 'statistics',
        'metrics', 'logs', 'log', 'logging', 'audit', 'audits', 'monitoring', 'monitor',
        'backup', 'backups', 'restore', 'sync', 'synchronize', 'batch', 'queue', 'jobs',
        'job', 'tasks', 'task', 'cron', 'scheduler', 'pipeline', 'workflow', 'workflows',
        'process', 'processes', 'operation', 'operations', 'transaction', 'transactions',
        'index', 'indices', 'cache', 'storage', 'store',
    },
    5: {  # Organizational / Informational
        'about', 'about-us', 'aboutus', 'contact', 'contact-us', 'contactus',
        'careers', 'career', 'jobs', 'job', 'team', 'staff', 'people', 'employees',
        'services', 'help', 'support', 'faq', 'faqs', 'terms', 'tos', 'privacy',
        'policy', 'policies', 'legal', 'disclaimer', 'sitemap', 'accessibility',
        'locations', 'location', 'offices', 'office', 'campus', 'site', 'sites',
        'departments', 'department', 'division', 'divisions', 'faculty', 'faculty-staff',
        'research', 'programs', 'program', 'resources', 'resource',
        'alumni', 'visitors', 'visitor', 'directory', 'map', 'maps',
        'mission', 'vision', 'history', 'overview', 'introduction', 'welcome',
        'community', 'partnership', 'partners', 'partner', 'sponsor', 'sponsors',
        'donate', 'donation', 'donations', 'volunteer', 'volunteers',
        'library', 'libraries', 'archive', 'archives', 'collection', 'collections',
        'health', 'wellness', 'safety', 'emergency', 'parking', 'transportation',
        'housing', 'dining', 'recreation', 'athletics', 'sports', 'student',
        'students', 'graduate', 'undergraduate', 'admissions', 'admission',
        'financial', 'finance', 'billing', 'payments', 'payroll', 'hr',
        'it', 'technology', 'engineering', 'science', 'arts', 'humanities',
        'medicine', 'medical', 'clinical', 'hospital', 'patient', 'patients',
        'doctor', 'doctors', 'nursing', 'pharmacy', 'laboratory', 'lab', 'labs',
        'government', 'municipal', 'city', 'county', 'state', 'federal',
        'department-of', 'bureau', 'agency', 'office-of', 'division-of',
    },
    6: {  # Temporal (YEAR token + date-related)
        'year', 'archive', 'archives', 'history',
        '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018',
        '2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026',
        'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
        'january', 'february', 'march', 'april', 'june', 'july', 'august',
        'september', 'october', 'november', 'december', 'quarterly', 'annual',
        'weekly', 'daily', 'monthly', 'q1', 'q2', 'q3', 'q4',
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
                 dropout: float, max_depth: int, vocab=None, n_segment_types: int = 8,
                 disable_segment_emb: bool = False):
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
        # disable_segment_emb: set True when vocab is large (>5K) and keyword coverage
        # is <5% — prevents the near-constant type-7 embedding from adding noise.
        self.disable_segment_emb = disable_segment_emb

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
        # Weight tying: share embedding and output projection weights.
        # Reduces parameters by vocab_size × d_model and improves
        # generalisation on small datasets (same technique used by LSTM baseline).
        self.fc = nn.Linear(d_model, vocab_size, bias=False)
        self.fc.weight = self.token_embedding.weight

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

        # fc.weight is tied to token_embedding.weight — no separate init needed.
        # fc.bias was removed (bias=False) since tied projections don't use bias.

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

        # Additive embedding combination
        x = (
            self.token_embedding(src)
            + self.depth_embedding(positions.expand(batch_size, -1))
        )

        # Segment embeddings: only added when meaningful coverage exists in vocab.
        # With large vocabs (>5K) the keyword lists cover <5% of tokens, so 99%+
        # of positions receive the type-7 embedding — effectively a constant bias
        # that adds noise rather than signal. Disabled by default for large vocabs.
        if not self.disable_segment_emb:
            seg_types = self.segment_type_buffer[src]                       # (batch, seq_len)
            x = x + self.segment_embedding(seg_types)
        x = self.emb_dropout(x)

        # Causal mask (bool): True = blocked position (upper triangle = future tokens).
        # NOTE: src_key_padding_mask is intentionally NOT used here.
        # The flat data format creates chunks where pos-0 can be a pad token; if pos-0
        # is also the only causally-visible key, softmax(-inf) = NaN. Since the LSTM
        # also attends through padding without masking, and CrossEntropyLoss ignores
        # padding via ignore_index=3, we match the same convention.
        # nn.Transformer.generate_square_subsequent_mask returns a float mask
        # (-inf above diagonal, 0 on/below). PyTorch 2.x prefers float over bool
        # for performance in _transformer_encoder_layer_fwd.
        causal_mask = nn.Transformer.generate_square_subsequent_mask(
            seq_len, device=src.device
        )

        x = self.transformer(x, mask=causal_mask)

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

    def segment_type_distribution(self, vocab=None) -> dict:
        """
        Diagnostic: return count of vocab tokens assigned to each segment type.

        Useful for verifying that type 7 (unknown) coverage is <30% of the vocab.
        Call this after model construction with the vocab used during training.

        Returns:
            dict mapping segment_type_idx -> {'count': int, 'tokens': list[str]}
        """
        buf = self.segment_type_buffer
        itos = vocab.get_itos() if vocab is not None else None

        distribution = {}
        for seg_type in range(self.n_segment_types):
            mask = (buf == seg_type).nonzero(as_tuple=True)[0]
            tokens = [itos[i.item()] for i in mask] if itos else []
            distribution[seg_type] = {'count': mask.numel(), 'tokens': tokens}
        return distribution


def diagnose_segment_coverage(vocab, n_segment_types: int = 8) -> None:
    """
    Print segment type distribution for a given vocabulary.
    Run this to verify type 7 (unknown) is <30% of total tokens.

    Usage:
        from transformer_pipeline.src.data import create_vocabulary
        from transformer_pipeline.src.model import diagnose_segment_coverage
        vocab = create_vocabulary(train_df, min_freq=3, max_depth=10)
        diagnose_segment_coverage(vocab)
    """
    itos = vocab.get_itos()
    type_names = {
        0: 'API/Versioned',
        1: 'Admin/Auth',
        2: 'Content/Publishing',
        3: 'Static assets',
        4: 'Data/Operations',
        5: 'Organizational',
        6: 'Temporal',
        7: 'Unknown (default)',
    }
    counts = {i: [] for i in range(n_segment_types)}
    for token in itos:
        seg = _TOKEN_TO_SEGMENT.get(token.lower(), 7)
        counts[seg].append(token)

    total = len(itos)
    print(f"\nSegment type coverage for vocab of {total} tokens:")
    print(f"{'Type':<4} {'Name':<25} {'Count':>6} {'Pct':>7}  Tokens (first 10)")
    print("-" * 80)
    for seg_type in range(n_segment_types):
        tokens = counts[seg_type]
        pct = 100.0 * len(tokens) / max(total, 1)
        preview = ', '.join(tokens[:10])
        flag = "  *** HIGH" if seg_type == 7 and pct > 30 else ""
        print(f"{seg_type:<4} {type_names[seg_type]:<25} {len(tokens):>6} {pct:>6.1f}%  {preview}{flag}")
    print()
