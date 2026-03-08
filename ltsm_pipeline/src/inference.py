"""
Inference: Generate predictions from trained LSTM models.
Replicates generate() function from LM_training.ipynb
"""

import torch


def generate(model, token_list, vocab, max_depth, model_max_depth, device,
             prediction_limit, seed=None):
    """
    Generate top-k predictions for next token(s).
    
    Args:
        model: LSTM model (must be in eval mode)
        token_list (list): Current token sequence (e.g., ['<sos>', 'api', 'v1'])
        vocab: Vocabulary object
        max_depth (int): Not used in this function (kept for API compatibility)
        model_max_depth (int): Max depth the model was trained on
        device: Device to run inference on
        prediction_limit (int): Number of top predictions to return
        seed (int): Random seed (optional)
        
    Returns:
        list: List of (probability, token) tuples, sorted by probability (descending)
    """
    if seed is not None:
        torch.manual_seed(seed)
    
    model.eval()
    
    # Convert tokens to indices
    indices = [vocab[t] for t in token_list]
    
    batch_size = 1
    hidden = model.init_hidden(batch_size, device)
    
    with torch.no_grad():
        # Forward pass
        src = torch.LongTensor([indices]).to(device)
        prediction, hidden = model(src, hidden)
        
        # Get logits for last position
        logits = prediction[:, -1, :]
        
        # Set special tokens to -inf to avoid predicting them
        eos_index = vocab['<eos>']
        sos_index = vocab['<sos>']
        unk_index = vocab['<unk>']
        pad_index = vocab['<pad>']
        
        logits[:, eos_index] = -float('inf')
        logits[:, sos_index] = -float('inf')
        logits[:, unk_index] = -float('inf')
        logits[:, pad_index] = -float('inf')
        
        # Softmax to get probabilities
        probs = torch.softmax(logits, dim=-1)
        
        # Get top-k predictions
        top_k = min(prediction_limit, probs.shape[-1])
        top_probs, top_indices = torch.topk(probs, top_k)
        
        # Convert indices to tokens and create (prob, token) pairs
        tokens = vocab.get_itos()
        prob_token_list = [
            (prob.item(), tokens[idx.item()])
            for prob, idx in zip(top_probs[0], top_indices[0])
        ]
        
        return prob_token_list
