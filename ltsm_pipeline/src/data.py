"""
Data loading, tokenization, vocabulary building, and DataLoader creation.
Replicates logic from LM_training.ipynb
"""

import os
import re
import pandas as pd
import torch
import torchtext
from torch.utils.data import TensorDataset, DataLoader


# Global constants
YEAR_TOKEN = 'YEAR'
SPECIAL_TOKENS = {
    '<unk>': 0,
    '<sos>': 1,
    '<eos>': 2,
    '<pad>': 3
}


def custom_tokenizer(path, max_depth):
    """
    Custom tokenizer to prepare directory paths.
    
    Args:
        path (str): Directory path (e.g., "/api/v1/users")
        max_depth (int): Maximum depth to trim to
        
    Returns:
        list: List of tokens
    """
    # Remove leading slash
    path = path.lstrip('/')
    
    # Split path into words
    path_words = path.split('/')
    
    # Trim to max_depth
    path_words = path_words[:max_depth]
    
    # Replace 4-digit numbers (years) with YEAR token
    for i, tok in enumerate(path_words):
        if re.match(r'^\d{4}$', tok):
            path_words[i] = YEAR_TOKEN
    
    return path_words


def yield_tokens(paths, max_depth):
    """
    Generator to yield tokenized paths.
    
    Args:
        paths: Iterable of path strings
        max_depth (int): Maximum depth for tokenization
        
    Yields:
        list: Tokenized path
    """
    for path in paths:
        yield custom_tokenizer(path, max_depth)


def create_vocabulary(train_df, min_freq, max_depth):
    """
    Create vocabulary from training data.
    
    Args:
        train_df (pd.DataFrame): Training dataframe with 'Path' column
        min_freq (int): Minimum frequency threshold
        max_depth (int): Maximum depth for tokenization
        
    Returns:
        torchtext.vocab.Vocab: Built vocabulary
    """
    vocab = torchtext.vocab.build_vocab_from_iterator(
        yield_tokens(train_df['Path'], max_depth),
        min_freq=min_freq
    )
    
    # Insert special tokens at specific indices
    vocab.insert_token('<unk>', 0)
    vocab.insert_token('<sos>', 1)
    vocab.insert_token('<eos>', 2)
    vocab.insert_token('<pad>', 3)
    vocab.set_default_index(vocab['<unk>'])
    
    return vocab


def get_dataloader(tokens, vocab, batch_size, seq_len):
    """
    Create PyTorch DataLoader from tokenized paths.
    
    Args:
        tokens (list): List of tokenized paths
        vocab: Vocabulary object
        batch_size (int): Batch size
        seq_len (int): Sequence length (max_depth + 2 for SOS/EOS)
        
    Returns:
        torch.Tensor: Data tensor of shape (batch_size, num_batches)
    """
    data = []
    
    for token_list in tokens:
        # Add EOS at end, SOS at beginning
        token_list = ['<sos>'] + token_list + ['<eos>']
        
        # Pad to seq_len
        while len(token_list) < seq_len:
            token_list.append('<pad>')
        
        # Trim to seq_len if too long
        token_list = token_list[:seq_len]
        
        # Map tokens to indices
        mapped_tokens = [vocab[token] for token in token_list]
        data.extend(mapped_tokens)
    
    data = torch.LongTensor(data)
    num_batches = data.shape[0] // batch_size
    data = data[:num_batches * batch_size]
    data = data.view(batch_size, num_batches)
    
    return data


def get_dataloaders(train_df, validation_df, min_freq, max_depth, batch_size):
    """
    Create train and validation dataloaders.
    
    Args:
        train_df (pd.DataFrame): Training data
        validation_df (pd.DataFrame): Validation data
        min_freq (int): Minimum frequency threshold
        max_depth (int): Maximum depth
        batch_size (int): Batch size
        
    Returns:
        tuple: (vocab, train_data, valid_data)
    """
    seq_len = max_depth + 2  # MAX_DEPTH + SOS + EOS
    
    vocab = create_vocabulary(train_df, min_freq, max_depth)
    
    # Tokenize datasets
    train_tokens = [custom_tokenizer(path, max_depth) for path in train_df['Path']]
    valid_tokens = [custom_tokenizer(path, max_depth) for path in validation_df['Path']]
    
    # Create dataloaders
    train_data = get_dataloader(train_tokens, vocab, batch_size, seq_len)
    valid_data = get_dataloader(valid_tokens, vocab, batch_size, seq_len)
    
    return vocab, train_data, valid_data


def load_datasets(data_folder):
    """
    Load train, validation, and test datasets.
    
    Args:
        data_folder (str): Path to folder containing train.csv, validation.csv, test.csv
        
    Returns:
        tuple: (train_df, validation_df, test_df)
    """
    # Support both flat layout:
    #   data_folder/train.csv
    # and nested layout used in this workspace:
    #   data_folder/train/train.csv
    train_path = os.path.join(data_folder, 'train.csv')
    validation_path = os.path.join(data_folder, 'validation.csv')
    test_path = os.path.join(data_folder, 'test.csv')

    if not os.path.exists(train_path):
        train_path = os.path.join(data_folder, 'train', 'train.csv')
    if not os.path.exists(validation_path):
        validation_path = os.path.join(data_folder, 'validation', 'validation.csv')
    if not os.path.exists(test_path):
        test_path = os.path.join(data_folder, 'test', 'test.csv')

    train_df = pd.read_csv(train_path)
    validation_df = pd.read_csv(validation_path)
    test_df = pd.read_csv(test_path)
    
    return train_df, validation_df, test_df


def get_test_by_domain(test_df):
    """
    Group test set by domain (Filename).
    
    Args:
        test_df (pd.DataFrame): Test dataframe with 'Filename' column
        
    Returns:
        list: List of dataframes, one per unique filename
    """
    test_df_list = []
    for filename in test_df['Filename'].unique():
        test_df_list.append(test_df[test_df['Filename'] == filename])
    return test_df_list
