"""
Directory tree construction from paths.
Replicates tree-builder functions from benchmarks.ipynb
"""

from anytree import Node


def create_tree(df):
    """
    Create directory tree from dataframe of paths.
    
    Args:
        df (pd.DataFrame): DataFrame with 'Path' column
        
    Returns:
        Node: Root node of tree
    """
    def get_or_create_node(name, parent=None):
        """Get existing child node or create new one."""
        children = parent.children if parent else []
        for child in children:
            if child.name == name:
                return child
        return Node(name, parent=parent)
    
    root = Node("/")
    paths = df['Path'].tolist()
    
    for path in paths:
        components = path.split("/")
        current_node = root
        for component in components:
            if component != "":
                current_node = get_or_create_node(component, current_node)
    
    return root


def create_tree_with_occurrences(df, root=None):
    """
    Create directory tree with occurrence counts.
    
    Args:
        df (pd.DataFrame): DataFrame with 'Path' column
        root (Node): Optional existing root node
        
    Returns:
        Node: Root node with count attributes
    """
    def get_or_create_node(name, parent):
        """Get existing child node (increment count) or create new one."""
        children = parent.children if parent else []
        for child in children:
            if child.name == name:
                child.count += 1
                return child
        return Node(name, parent=parent, count=1)
    
    if root is None:
        root = Node("/", count=1)
    
    paths = df['Path'].tolist()
    
    for path in paths:
        components = path.split("/")
        current_node = root
        for component in components:
            if component != "":
                current_node = get_or_create_node(component, current_node)
    
    return root


def create_wordlist_tree(wordlist_file, train_root):
    """
    Create tree from wordlist, using training tree as guide.
    Only includes words that exist in training tree.
    
    Args:
        wordlist_file (str): Path to wordlist file (one word per line)
        train_root (Node): Root of training tree
        
    Returns:
        Node: Root node with wordlist words
    """
    with open(wordlist_file, 'r') as f:
        wordlist = [line.strip() for line in f]
    
    root = Node("/")
    
    def add_node(current_node, train_node):
        """Recursively add nodes that exist in training tree."""
        # Map training node children by name
        children_dict = {child.name: child for child in train_node.children}
        
        # Add wordlist words if they exist in training tree
        for word in wordlist:
            if word in children_dict:
                child = Node(word, parent=current_node, count=children_dict[word].count)
                add_node(child, children_dict[word])
    
    add_node(root, train_root)
    return root
