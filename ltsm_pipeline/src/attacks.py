"""
Attack simulation functions for directory enumeration.
Replicates attack algorithms from benchmarks.ipynb
"""

import queue
import heapq
import random
import re
from queue import LifoQueue

from .inference import generate
from .data import YEAR_TOKEN


def breadth_first_attack(wordlist_file, root, request_limit=100000):
    """
    Breadth-first directory attack baseline.
    
    Args:
        wordlist_file (str): Path to wordlist file
        root: Root node of test tree
        request_limit (int): Max requests allowed
        
    Returns:
        tuple: (requests_list, successful_list, failed_list, time)
    """
    with open(wordlist_file, 'r') as f:
        wordlist = [line.strip() for line in f]
    
    total_requests = 0
    successful_responses = 0
    failed_responses = 0
    
    total_requests_list = []
    successful_responses_list = []
    failed_responses_list = []
    
    def simulate(word, node):
        nonlocal total_requests, successful_responses, failed_responses
        
        total_requests += 1
        children_map = {c.name: c for c in node.children}
        
        if word in children_map:
            successful_responses += 1
            return children_map[word]
        else:
            failed_responses += 1
        
        return None
    
    q = queue.Queue()
    
    # Enqueue all wordlist words at root
    for word in wordlist:
        q.put((word, root))
    
    # BFS loop
    while not q.empty() and total_requests < request_limit:
        word, node = q.get()
        new_node = simulate(word, node)
        
        if new_node is not None:
            # Recursive search: add children with all wordlist words
            for new_word in wordlist:
                q.put((new_word, new_node))
        
        # Record metrics every 20 requests
        if total_requests == 1 or (total_requests - 1) % 20 == 0:
            total_requests_list.append(total_requests)
            successful_responses_list.append(successful_responses)
            failed_responses_list.append(failed_responses)
    
    return total_requests_list, successful_responses_list, failed_responses_list, 0


def depth_first_attack(wordlist_file, root, request_limit=100000):
    """
    Depth-first directory attack baseline.
    
    Args:
        wordlist_file (str): Path to wordlist file
        root: Root node of test tree
        request_limit (int): Max requests allowed
        
    Returns:
        tuple: (requests_list, successful_list, failed_list, time)
    """
    with open(wordlist_file, 'r') as f:
        wordlist = [line.strip() for line in f]
    
    total_requests = 0
    successful_responses = 0
    failed_responses = 0
    
    total_requests_list = []
    successful_responses_list = []
    failed_responses_list = []
    
    def simulate(word, node):
        nonlocal total_requests, successful_responses, failed_responses
        
        total_requests += 1
        children_map = {c.name: c for c in node.children}
        
        if word in children_map:
            successful_responses += 1
            return children_map[word]
        else:
            failed_responses += 1
        
        return None
    
    q = LifoQueue()  # LIFO for depth-first
    
    # Enqueue all wordlist words at root
    for word in wordlist:
        q.put((word, root))
    
    # DFS loop
    while not q.empty() and total_requests < request_limit:
        word, node = q.get()
        new_node = simulate(word, node)
        
        if new_node is not None:
            # Recursive search: add children with all wordlist words
            for new_word in wordlist:
                q.put((new_word, new_node))
        
        # Record metrics every 20 requests
        if total_requests == 1 or (total_requests - 1) % 20 == 0:
            total_requests_list.append(total_requests)
            successful_responses_list.append(successful_responses)
            failed_responses_list.append(failed_responses)
    
    return total_requests_list, successful_responses_list, failed_responses_list, 0


def lm_attack(model, vocab, max_depth, test_root, device, request_limit=100000,
              prediction_limit=500, custom_tokenizer=None):
    """
    Language model-based directory attack.
    Uses LSTM predictions to prioritize directories.
    
    Args:
        model: LSTM model
        vocab: Vocabulary
        max_depth (int): Max depth model was trained on
        test_root: Root of test tree
        device: Device to run inference on
        request_limit (int): Max requests allowed
        prediction_limit (int): Number of predictions to consider
        custom_tokenizer (callable): Tokenizer function
        
    Returns:
        tuple: (requests_list, successful_list, failed_list, time)
    """
    from .data import custom_tokenizer as default_tokenizer
    
    if custom_tokenizer is None:
        custom_tokenizer = default_tokenizer
    
    total_requests = 0
    successful_responses = 0
    failed_responses = 0
    
    total_requests_list = []
    successful_responses_list = []
    failed_responses_list = []
    
    def simulate(word, node):
        nonlocal total_requests, successful_responses, failed_responses
        
        total_requests += 1
        
        # Handle YEAR token in node names
        children_map = {}
        for c in node.children:
            name = c.name
            pattern = r'^\d{4}$'
            if re.match(pattern, name):
                name = YEAR_TOKEN
            children_map[name] = c
        
        if word in children_map:
            successful_responses += 1
            return word, children_map[word]
        else:
            failed_responses += 1
        
        return None, None
    
    # Initialize heap with starting predictions
    predictions = generate(model, ['<sos>'], vocab, max_depth, max_depth, device,
                          prediction_limit)
    
    heap = [(-prob, 1, word, ['<sos>'], test_root) for prob, word in predictions]
    heapq.heapify(heap)
    
    # Attack loop
    while len(heap) > 0 and total_requests < request_limit:
        _, depth, word, token_list, target = heapq.heappop(heap)
        
        child_name, new_node = simulate(word, target)
        
        if new_node is not None:
            # Found directory! Get predictions for next level
            new_token_list = token_list + [child_name]
            predictions = generate(model, new_token_list, vocab, max_depth, max_depth,
                                  device, prediction_limit)
            
            # Add predictions to heap
            for prob, pred_word in predictions:
                heapq.heappush(heap, (-prob, len(new_token_list), pred_word,
                                     new_token_list, new_node))
        
        # Record metrics every 20 requests
        if total_requests == 1 or (total_requests - 1) % 20 == 0:
            total_requests_list.append(total_requests)
            successful_responses_list.append(successful_responses)
            failed_responses_list.append(failed_responses)
    
    return total_requests_list, successful_responses_list, failed_responses_list, 0
