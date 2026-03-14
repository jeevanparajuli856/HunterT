"""
Inference: Generate predictions from a trained DirHunterT transformer model.

Interface is identical to ltsm_pipeline/src/inference.py so the same
lm_attack() function in attacks.py works without modification.
"""

import torch


def generate(model, token_list, vocab, max_depth, model_max_depth, device,
             prediction_limit, seed=None):
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

        probs = torch.softmax(logits, dim=-1)

        top_k = min(prediction_limit, probs.shape[-1])
        top_probs, top_indices = torch.topk(probs, top_k)

        itos = vocab.get_itos()
        return [
            (prob.item(), itos[idx.item()])
            for prob, idx in zip(top_probs[0], top_indices[0])
        ]
