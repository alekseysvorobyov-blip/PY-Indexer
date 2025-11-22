#!/usr/bin/env python3
"""
Hash utilities for PY-Indexer v3.0.

Provides hashing functions for:
- Object content hashing (classes, functions)
- File hashing
- Configurable hash lengths (8, 16, 32, 64 characters)
- SHA256 algorithm

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

import hashlib
from pathlib import Path

from utils.utils_logger import get_logger

logger = get_logger(__name__)


def hash_object(content: str, length: int = 16) -> str:
    """
    Calculate hash of object content.
    
    Uses SHA256 and truncates to specified length.
    
    Parameters
    ----------
    content : str
        String content to hash (e.g., function source code)
    length : int, optional
        Hash length in characters: 8, 16, 32, or 64 (default: 16)
        
    Returns
    -------
    str
        Hexadecimal hash string of specified length
        
    Raises
    ------
    ValueError
        If length is not one of: 8, 16, 32, 64
        
    Examples
    --------
    >>> code = "def example(): pass"
    >>> hash_val = hash_object(code, length=16)
    >>> print(len(hash_val))
    16
    
    >>> hash_val = hash_object(code, length=8)
    >>> print(len(hash_val))
    8
    """
    valid_lengths = [8, 16, 32, 64]
    if length not in valid_lengths:
        logger.error(f"Invalid hash length: {length}")
        raise ValueError(f"Invalid hash length: {length}. Must be one of: {valid_lengths}")
    
    try:
        hash_obj = hashlib.sha256(content.encode('utf-8'))
        full_hash = hash_obj.hexdigest()
        truncated_hash = full_hash[:length]
        
        logger.debug(f"Hashed content (length={length}): {truncated_hash}")
        return truncated_hash
    except Exception as e:
        logger.error(f"Error hashing content: {e}", exc_info=True)
        raise


def hash_file(file_path: str | Path, length: int = 16) -> str:
    """
    Calculate hash of file content.
    
    Uses SHA256 and truncates to specified length.
    Reads file in chunks for memory efficiency.
    
    Parameters
    ----------
    file_path : str | Path
        Path to file
    length : int, optional
        Hash length in characters: 8, 16, 32, or 64 (default: 16)
        
    Returns
    -------
    str
        Hexadecimal hash string of specified length
        
    Raises
    ------
    FileNotFoundError
        If file doesn't exist
    ValueError
        If length is invalid
        
    Examples
    --------
    >>> hash_val = hash_file("module.py", length=16)
    >>> print(hash_val)
    'a3c5f7b2d1e4f6a8'
    """
    valid_lengths = [8, 16, 32, 64]
    if length not in valid_lengths:
        logger.error(f"Invalid hash length: {length}")
        raise ValueError(f"Invalid hash length: {length}. Must be one of: {valid_lengths}")
    
    path = Path(file_path)
    
    if not path.exists():
        logger.error(f"File not found: {path}")
        raise FileNotFoundError(f"File not found: {path}")
    
    if not path.is_file():
        logger.error(f"Not a file: {path}")
        raise ValueError(f"Not a file: {path}")
    
    try:
        hash_obj = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        
        full_hash = hash_obj.hexdigest()
        truncated_hash = full_hash[:length]
        
        logger.debug(f"Hashed file {path} (length={length}): {truncated_hash}")
        return truncated_hash
    except Exception as e:
        logger.error(f"Error hashing file {path}: {e}", exc_info=True)
        raise


def hash_string_list(strings: list[str], length: int = 16) -> str:
    """
    Calculate hash of list of strings.
    
    Joins strings with newlines before hashing.
    Useful for hashing function signatures, parameter lists, etc.
    
    Parameters
    ----------
    strings : list[str]
        List of strings to hash
    length : int, optional
        Hash length in characters: 8, 16, 32, or 64 (default: 16)
        
    Returns
    -------
    str
        Hexadecimal hash string of specified length
        
    Raises
    ------
    ValueError
        If length is invalid
        
    Examples
    --------
    >>> params = ["user_id: int", "name: str", "email: str"]
    >>> hash_val = hash_string_list(params, length=8)
    >>> print(hash_val)
    'a3c5f7b2'
    """
    valid_lengths = [8, 16, 32, 64]
    if length not in valid_lengths:
        logger.error(f"Invalid hash length: {length}")
        raise ValueError(f"Invalid hash length: {length}. Must be one of: {valid_lengths}")
    
    try:
        combined = '\n'.join(strings)
        return hash_object(combined, length)
    except Exception as e:
        logger.error(f"Error hashing string list: {e}", exc_info=True)
        raise


def validate_hash_length(length: int) -> bool:
    """
    Validate hash length parameter.
    
    Parameters
    ----------
    length : int
        Hash length to validate
        
    Returns
    -------
    bool
        True if length is valid, False otherwise
        
    Examples
    --------
    >>> validate_hash_length(16)
    True
    
    >>> validate_hash_length(12)
    False
    """
    valid_lengths = [8, 16, 32, 64]
    is_valid = length in valid_lengths
    
    if not is_valid:
        logger.warning(f"Invalid hash length: {length}. Valid lengths: {valid_lengths}")
    
    return is_valid
