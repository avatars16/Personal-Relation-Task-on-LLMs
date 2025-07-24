"""
Utility functions for file I/O operations.
"""

import os
from constants import DEFAULT_OUTPUT_DIR

# Global variable to store the current base output directory
_current_base_dir = None

def set_base_output_directory(base_dir):
    """
    Set the global base output directory for all subsequent calls to get_output_directory.
    
    Args:
        base_dir (str): The base output directory path
    """
    global _current_base_dir
    _current_base_dir = base_dir

def get_output_directory(subdir='', base_dir=None):
    """
    Create and return path to output directory with optional subdirectory.
    
    Args:
        subdir (str): Optional subdirectory name
        base_dir (str): Optional base output directory. If None, uses the global base dir or DEFAULT_OUTPUT_DIR
        
    Returns:
        str: Path to the output directory
    """
    if base_dir is None:
        base_dir = _current_base_dir if _current_base_dir is not None else DEFAULT_OUTPUT_DIR
    
    output_path = os.path.join(base_dir, subdir) if subdir else base_dir
    os.makedirs(output_path, exist_ok=True)
    return output_path
