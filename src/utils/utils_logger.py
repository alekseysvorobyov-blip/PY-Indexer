#!/usr/bin/env python3
"""
Logging utilities for PY-Indexer v3.0.

Provides centralized logging configuration with:
- Single log file: main.log
- DEBUG level by default
- Console output duplication
- UTF-8 encoding
- Standardized format

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    log_file: str = "main.log",
    level: int = logging.DEBUG,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Setup logger with file and console handlers.
    
    Parameters
    ----------
    name : str
        Logger name (typically __name__ of the module)
    log_file : str, optional
        Path to log file (default: "main.log")
    level : int, optional
        Logging level (default: logging.DEBUG)
    format_string : str, optional
        Custom format string. If None, uses default format.
        
    Returns
    -------
    logging.Logger
        Configured logger instance
        
    Examples
    --------
    >>> logger = setup_logger(__name__)
    >>> logger.info("Application started")
    >>> logger.debug("Debug information")
    >>> logger.error("Error occurred", exc_info=True)
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    # Create formatters
    formatter = logging.Formatter(format_string)
    
    # File handler - append mode, UTF-8 encoding
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (IOError, OSError) as e:
        print(f"WARNING: Cannot create log file {log_file}: {e}", file=sys.stderr)
    
    # Console handler - stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get existing logger by name.
    
    If logger doesn't exist, creates new one with default settings.
    
    Parameters
    ----------
    name : str
        Logger name (typically __name__ of the module)
        
    Returns
    -------
    logging.Logger
        Logger instance
        
    Examples
    --------
    >>> logger = get_logger(__name__)
    >>> logger.info("Using existing logger")
    """
    logger = logging.getLogger(name)
    
    # If logger has no handlers, set it up with defaults
    if not logger.handlers:
        return setup_logger(name)
    
    return logger


def configure_root_logger(
    log_file: str = "main.log",
    level: int = logging.DEBUG
) -> None:
    """
    Configure root logger for entire application.
    
    Should be called once at application startup.
    All module loggers will inherit this configuration.
    
    Parameters
    ----------
    log_file : str, optional
        Path to log file (default: "main.log")
    level : int, optional
        Logging level (default: logging.DEBUG)
        
    Examples
    --------
    >>> configure_root_logger("main.log", logging.DEBUG)
    >>> # Now all loggers in all modules will use this configuration
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8', mode='a'),
            logging.StreamHandler(sys.stdout)
        ]
    )


def set_log_level(logger: logging.Logger, level_name: str) -> None:
    """
    Change log level dynamically.
    
    Parameters
    ----------
    logger : logging.Logger
        Logger instance to modify
    level_name : str
        Level name: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        
    Raises
    ------
    ValueError
        If level_name is invalid
        
    Examples
    --------
    >>> logger = get_logger(__name__)
    >>> set_log_level(logger, "INFO")
    >>> # Now logger will only show INFO and above
    """
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    level_upper = level_name.upper()
    if level_upper not in level_map:
        raise ValueError(
            f"Invalid log level: {level_name}. "
            f"Valid levels: {', '.join(level_map.keys())}"
        )
    
    level = level_map[level_upper]
    logger.setLevel(level)
    
    # Update all handlers
    for handler in logger.handlers:
        handler.setLevel(level)


# Module-level logger for this utils module
logger = setup_logger(__name__)
