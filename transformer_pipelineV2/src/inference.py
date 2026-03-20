"""
Inference: Generate predictions from a trained DirHunterT transformer model.

Interface is identical to ltsm_pipeline/src/inference.py so the same
lm_attack() function in attacks.py works without modification.
"""

import torch


def generate(model, token_list, vocab, max_depth, model_max_depth, device,
             prediction_limit, seed=None, temperature=1.0):
    """
    Generate top-k predictions for the next directory token.

    Args:
        model:                DirHunterT model (must be in eval mode)
        token_list (list):    Current token sequence, e.g. ['<sos>', 'api', 'v1']
        vocab:                torchtext vocabulary object
        max_depth (int):      Not used — kept for API compatibility with LSTM version
        model_max_depth (int):Max depth the model was trained on (unused, kept for compat)
        device:               Torch device
        prediction_limit (int):Number of top predictions to return
        seed (int):           Optional random seed
        temperature (float):  Softmax temperature (default=1.0). <1 sharpens, >1 flattens.

    Returns:
        list: [(probability, token_string), ...] sorted descending by probability
    """
    if seed is not None:
        torch.manual_seed(seed)

    model.eval()

    # Map token strings to indices (OOV → <unk> index 0, same as LSTM)
    indices = [vocab[t] for t in token_list]

    with torch.no_grad():
        src = torch.LongTensor([indices]).to(device)   # (1, seq_len)
        prediction, _ = model(src, None)               # (1, seq_len, vocab_size)

        # Use logits at the last sequence position (next-token prediction)
        logits = prediction[:, -1, :]                  # (1, vocab_size)

        # Mask special tokens so they are never predicted as next directory
        for special in ('<eos>', '<sos>', '<unk>', '<pad>'):
            logits[:, vocab[special]] = float('-inf')

        # Temperature scaling: divide logits before softmax
        if temperature != 1.0 and temperature > 0:
            logits = logits / temperature

        probs = torch.softmax(logits, dim=-1)

        top_k = min(prediction_limit, probs.shape[-1])
        top_probs, top_indices = torch.topk(probs, top_k)

        itos = vocab.get_itos()
        return [
            (prob.item(), itos[idx.item()])
            for prob, idx in zip(top_probs[0], top_indices[0])
        ]


def beam_search_generate(model, token_list, vocab, device, prediction_limit,
                         beam_width=5, temperature=1.0):
    """
    Beam search inference for next-token prediction.

    Unlike greedy top-K, beam search explores multiple hypothesis branches
    simultaneously. The transformer's stateless nature makes this more
    efficient than for LSTMs (no hidden state replay needed).

    Args:
        model:                DirHunterT model (must be in eval mode)
        token_list (list):    Current token sequence, e.g. ['<sos>', 'api', 'v1']
        vocab:                torchtext vocabulary object
        device:               Torch device
        prediction_limit (int):Number of top predictions to return (final output size)
        beam_width (int):     Number of beams to maintain (default=5)
        temperature (float):  Softmax temperature applied at each step

    Returns:
        list: [(probability, token_string), ...] sorted descending by probability
              Length = min(prediction_limit, vocab_size - 4 special tokens)

    Note:
        This function predicts only the NEXT single token (depth+1), using beam
        search to score each candidate by exploring one step further.
        The score for candidate token t is: P(t | prefix) * max_t2 P(t2 | prefix+t).
        This reranks candidates by their "look-ahead" quality.
    """
    model.eval()
    itos = vocab.get_itos()
    special_tokens = {'<eos>', '<sos>', '<unk>', '<pad>'}
    special_indices = {vocab[s] for s in special_tokens}

    base_indices = [vocab[t] for t in token_list]

    with torch.no_grad():
        # --- Step 1: Get first-token logits ---
        src = torch.LongTensor([base_indices]).to(device)         # (1, seq_len)
        out, _ = model(src, None)
        logits = out[:, -1, :].clone()                            # (1, vocab_size)
        for idx in special_indices:
            logits[:, idx] = float('-inf')
        if temperature != 1.0 and temperature > 0:
            logits = logits / temperature
        log_probs = torch.log_softmax(logits, dim=-1)             # (1, vocab_size)

        # Keep top beam_width candidates from the first step
        top_log_probs, top_indices = torch.topk(log_probs[0], min(beam_width, log_probs.shape[-1]))

        # beams: list of (cumulative_log_prob, [token_idx, ...])
        beams = [(lp.item(), [idx.item()]) for lp, idx in zip(top_log_probs, top_indices)]

        # --- Step 2: One look-ahead step to rerank beams ---
        extended_scores = []
        for cum_lp, token_seq in beams:
            next_indices = base_indices + token_seq
            src2 = torch.LongTensor([next_indices]).to(device)
            out2, _ = model(src2, None)
            logits2 = out2[:, -1, :].clone()
            for idx in special_indices:
                logits2[:, idx] = float('-inf')
            if temperature != 1.0 and temperature > 0:
                logits2 = logits2 / temperature
            log_probs2 = torch.log_softmax(logits2, dim=-1)
            # Score = current log_prob + max future log_prob (optimistic look-ahead)
            look_ahead = log_probs2.max().item()
            extended_scores.append((cum_lp + look_ahead, cum_lp, token_seq[0]))

        # Sort by extended score, take top prediction_limit
        extended_scores.sort(key=lambda x: x[0], reverse=True)
        top_n = extended_scores[:prediction_limit]

        # Convert log-probs back to probabilities (re-normalise for output)
        raw_probs = [(_lp, _tok) for (_, _lp, _tok) in top_n]
        max_lp = max(lp for lp, _ in raw_probs)
        probs_exp = [(lp - max_lp, tok) for lp, tok in raw_probs]
        total = sum(2.718281828 ** lp for lp, _ in probs_exp)
        results = [(2.718281828 ** lp / total, itos[tok]) for lp, tok in probs_exp]

    return results
