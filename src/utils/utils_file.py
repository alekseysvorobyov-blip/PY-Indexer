#!/usr/bin/env python3
"""
File utilities for PY-Indexer v3.0 - UPDATED with file size protection.

Provides file operations with:
- Multiple encoding fallback (UTF-8, CP1251, Latin-1)
- File size validation (protection from huge files)
- Directory creation with validation
- File hash calculation
- File modification time retrieval
- Safe file reading

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

from utils.utils_logger import get_logger

logger = get_logger(__name__)

# Default max file size (1 MB) - can be overridden from config
DEFAULT_MAX_FILE_SIZE = 1048576  # 1 MB in bytes


def read_python_file(file_path: str | Path, max_size: int = DEFAULT_MAX_FILE_SIZE) -> str:
    """
    Read Python file with encoding fallback and size protection.
    
    Tries encodings in order: UTF-8 -> CP1251 -> Latin-1
    Protects against reading extremely large files.
    
    Parameters
    ----------
    file_path : str | Path
        Path to Python file
    max_size : int, optional
        Maximum file size in bytes (default: 1 MB)
        
    Returns
    -------
    str
        File content as string
        
    Raises
    ------
    FileNotFoundError
        If file doesn't exist
    ValueError
        If file cannot be decoded with any supported encoding OR file too large
        
    Examples
    --------
    >>> content = read_python_file("module.py")
    >>> print(len(content))
    1234
    
    >>> content = read_python_file("module.py", max_size=5242880)  # 5 MB
    >>> print(len(content))
    2048000
    """
    path = Path(file_path)
    
    if not path.exists():
        logger.error(f"File not found: {path}")
        raise FileNotFoundError(f"File not found: {path}")
    
    if not path.is_file():
        logger.error(f"Not a file: {path}")
        raise ValueError(f"Not a file: {path}")
    
    # Check file size BEFORE reading
    file_size = path.stat().st_size
    if file_size > max_size:
        logger.error(
            f"File too large: {path} ({file_size} bytes > {max_size} bytes limit). "
            f"Skipping to prevent memory issues."
        )
        raise ValueError(
            f"File too large: {path} ({file_size} bytes > {max_size} bytes limit). "
            f"Increase max_file_size in pyproject.toml if needed."
        )
    
    logger.debug(f"File size OK: {path} ({file_size} bytes)")
    
    encodings = ['utf-8', 'cp1251', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            logger.debug(f"Successfully read {path} with {encoding} encoding")
            return content
        except UnicodeDecodeError:
            logger.debug(f"Failed to read {path} with {encoding}, trying next encoding")
            continue
        except Exception as e:
            logger.error(f"Unexpected error reading {path} with {encoding}: {e}", exc_info=True)
            continue
    
    logger.error(f"Cannot decode file {path} with any supported encoding")
    raise ValueError(f"Cannot decode file {path} with any supported encoding: {encodings}")


def ensure_directory(path: str | Path) -> None:
    """
    Create directory if it doesn't exist.
    
    Creates parent directories as needed.
    
    Parameters
    ----------
    path : str | Path
        Directory path to create
        
    Raises
    ------
    OSError
        If directory cannot be created
        
    Examples
    --------
    >>> ensure_directory("output/indexes")
    >>> # Creates output/ and output/indexes/
    """
    dir_path = Path(path)
    
    if dir_path.exists():
        if not dir_path.is_dir():
            logger.error(f"Path exists but is not a directory: {dir_path}")
            raise ValueError(f"Path exists but is not a directory: {dir_path}")
        logger.debug(f"Directory already exists: {dir_path}")
        return
    
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")
    except OSError as e:
        logger.error(f"Cannot create directory {dir_path}: {e}", exc_info=True)
        raise


def get_file_hash(file_path: str | Path, algorithm: str = 'sha256') -> str:
    """
    Calculate file hash.
    
    Parameters
    ----------
    file_path : str | Path
        Path to file
    algorithm : str, optional
        Hash algorithm: 'sha256', 'md5', 'sha1' (default: 'sha256')
        
    Returns
    -------
    str
        Hexadecimal hash string
        
    Raises
    ------
    FileNotFoundError
        If file doesn't exist
    ValueError
        If algorithm is unsupported
        
    Examples
    --------
    >>> hash_val = get_file_hash("module.py")
    >>> print(hash_val)
    'a3c5f7...'
    """
    path = Path(file_path)
    
    if not path.exists():
        logger.error(f"File not found: {path}")
        raise FileNotFoundError(f"File not found: {path}")
    
    if not path.is_file():
        logger.error(f"Not a file: {path}")
        raise ValueError(f"Not a file: {path}")
    
    supported_algorithms = ['sha256', 'md5', 'sha1']
    if algorithm not in supported_algorithms:
        logger.error(f"Unsupported hash algorithm: {algorithm}")
        raise ValueError(f"Unsupported algorithm: {algorithm}. Supported: {supported_algorithms}")
    
    try:
        hash_obj = hashlib.new(algorithm)
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        
        hash_value = hash_obj.hexdigest()
        logger.debug(f"Calculated {algorithm} hash for {path}: {hash_value[:16]}...")
        return hash_value
    except Exception as e:
        logger.error(f"Error calculating hash for {path}: {e}", exc_info=True)
        raise


def get_file_modified(file_path: str | Path, iso_format: bool = True) -> str:
    """
    Get file last modification time.
    
    Parameters
    ----------
    file_path : str | Path
        Path to file
    iso_format : bool, optional
        Return ISO-8601 format if True, else human-readable (default: True)
        
    Returns
    -------
    str
        Modification time as string
        
    Raises
    ------
    FileNotFoundError
        If file doesn't exist
        
    Examples
    --------
    >>> mod_time = get_file_modified("module.py")
    >>> print(mod_time)
    '2025-11-22T15:30:45Z'
    
    >>> mod_time = get_file_modified("module.py", iso_format=False)
    >>> print(mod_time)
    '2025-11-22 15:30:45'
    """
    path = Path(file_path)
    
    if not path.exists():
        logger.error(f"File not found: {path}")
        raise FileNotFoundError(f"File not found: {path}")
    
    try:
        timestamp = path.stat().st_mtime
        dt = datetime.fromtimestamp(timestamp)
        
        if iso_format:
            result = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            result = dt.strftime('%Y-%m-%d %H:%M:%S')
        
        logger.debug(f"File {path} modified at: {result}")
        return result
    except Exception as e:
        logger.error(f"Error getting modification time for {path}: {e}", exc_info=True)
        raise


def get_file_size(file_path: str | Path) -> int:
    """
    Get file size in bytes.
    
    Parameters
    ----------
    file_path : str | Path
        Path to file
        
    Returns
    -------
    int
        File size in bytes
        
    Raises
    ------
    FileNotFoundError
        If file doesn't exist
        
    Examples
    --------
    >>> size = get_file_size("module.py")
    >>> print(f"File size: {size} bytes")
    File size: 2048 bytes
    """
    path = Path(file_path)
    
    if not path.exists():
        logger.error(f"File not found: {path}")
        raise FileNotFoundError(f"File not found: {path}")
    
    if not path.is_file():
        logger.error(f"Not a file: {path}")
        raise ValueError(f"Not a file: {path}")
    
    try:
        size = path.stat().st_size
        logger.debug(f"File {path} size: {size} bytes")
        return size
    except Exception as e:
        logger.error(f"Error getting size for {path}: {e}", exc_info=True)
        raise


def find_python_files(directory: str | Path, recursive: bool = True) -> list[Path]:
    """
    Find all Python files in directory.
    
    Parameters
    ----------
    directory : str | Path
        Directory to search
    recursive : bool, optional
        Search subdirectories if True (default: True)
        
    Returns
    -------
    list[Path]
        List of Python file paths
        
    Raises
    ------
    FileNotFoundError
        If directory doesn't exist
    ValueError
        If path is not a directory
        
    Examples
    --------
    >>> files = find_python_files("src/")
    >>> print(len(files))
    42
    
    >>> files = find_python_files("src/", recursive=False)
    >>> print(len(files))
    5
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        logger.error(f"Directory not found: {dir_path}")
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    if not dir_path.is_dir():
        logger.error(f"Not a directory: {dir_path}")
        raise ValueError(f"Not a directory: {dir_path}")
    
    try:
        if recursive:
            pattern = '**/*.py'
        else:
            pattern = '*.py'
        
        files = list(dir_path.glob(pattern))
        logger.info(f"Found {len(files)} Python files in {dir_path} (recursive={recursive})")
        return files
    except Exception as e:
        logger.error(f"Error finding Python files in {dir_path}: {e}", exc_info=True)
        raise


def validate_path_safety(path: str | Path) -> bool:
    """
    Validate path doesn't contain directory traversal attempts.
    
    Checks for '..' and absolute path attempts.
    
    Parameters
    ----------
    path : str | Path
        Path to validate
        
    Returns
    -------
    bool
        True if path is safe, False otherwise
        
    Examples
    --------
    >>> validate_path_safety("src/module.py")
    True
    
    >>> validate_path_safety("../../../etc/passwd")
    False
    
    >>> validate_path_safety("/etc/passwd")
    False
    """
    path_str = str(path)
    
    # Check for directory traversal
    if '..' in path_str:
        logger.warning(f"Path contains directory traversal: {path_str}")
        return False
    
    # Check for absolute paths (potential security risk)
    path_obj = Path(path_str)
    if path_obj.is_absolute():
        logger.warning(f"Path is absolute: {path_str}")
        return False
    
    logger.debug(f"Path is safe: {path_str}")
    return True


def get_relative_path(file_path: str | Path, base_path: str | Path) -> str:
    """
    Get relative path from base path.
    
    Parameters
    ----------
    file_path : str | Path
        Full file path
    base_path : str | Path
        Base directory path
        
    Returns
    -------
    str
        Relative path with forward slashes
        
    Examples
    --------
    >>> rel = get_relative_path("/project/src/module.py", "/project")
    >>> print(rel)
    'src/module.py'
    """
    file_path_obj = Path(file_path).resolve()
    base_path_obj = Path(base_path).resolve()
    
    try:
        relative = file_path_obj.relative_to(base_path_obj)
        # Use forward slashes for cross-platform compatibility
        result = str(relative).replace('\\', '/')
        logger.debug(f"Relative path: {result}")
        return result
    except ValueError as e:
        logger.error(f"Cannot compute relative path: {file_path} relative to {base_path}: {e}")
        raise
