#!/usr/bin/env python3
"""
Configuration Loader for PY-Indexer v3.0.

Loads configuration from pyproject.toml with validation and defaults.

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback для Python 3.10
    except ImportError:
        tomllib = None

from pathlib import Path
from typing import Any, Optional

from utils.utils_logger import get_logger

logger = get_logger(__name__)


class Config:
    """
    Configuration manager for PY-Indexer.
    
    Loads settings from pyproject.toml with validation and provides typed access.
    """
    
    # Default values (fallback if pyproject.toml is missing)
    DEFAULTS = {
        'log_level': 'DEBUG',
        'log_file': 'main.log',
        'max_file_size': 1048576,  # 1 MB
        'max_ast_depth': 100,
        'default_hash_length': 16,
        'default_format': 'json',
        'minify_output': False,
        'compress_names': False,
        'encoding_fallbacks': ['utf-8', 'cp1251', 'latin-1'],
        'parse_timeout': 30
    }
    
    # Validation rules
    VALIDATION_RULES = {
        'max_file_size': lambda x: isinstance(x, int) and x > 0,
        'max_ast_depth': lambda x: isinstance(x, int) and x > 0,
        'default_hash_length': lambda x: x in [8, 16, 32, 64],
        'default_format': lambda x: x in ['json', 'json.gz', 'msgpack'],
        'parse_timeout': lambda x: isinstance(x, int) and x > 0,
        'log_level': lambda x: x in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    }
    
    def __init__(self, config_path: Optional[str | Path] = None):
        """
        Initialize configuration.
        
        Parameters
        ----------
        config_path : str | Path, optional
            Path to pyproject.toml (default: searches in current and parent dirs)
        """
        self.logger = get_logger(__name__)
        self._config = {}
        self._load_config(config_path)
    
    def _load_config(self, config_path: Optional[str | Path] = None) -> None:
        """
        Load configuration from pyproject.toml.
        
        Parameters
        ----------
        config_path : str | Path, optional
            Path to pyproject.toml
        """
        if tomllib is None:
            self.logger.warning("tomllib/tomli not available, using defaults")
            self._config = self.DEFAULTS.copy()
            return
        
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = self._find_config_file()
        
        if not config_file or not config_file.exists():
            self.logger.warning("Configuration file not found, using defaults")
            self._config = self.DEFAULTS.copy()
            return
        
        try:
            with open(config_file, 'rb') as f:
                data = tomllib.load(f)
            
            # Extract py-indexer configuration
            if 'tool' in data and 'py-indexer' in data['tool']:
                raw_config = data['tool']['py-indexer']
                self._config = self._validate_config(raw_config)
                self.logger.info(f"Configuration loaded from {config_file}")
            else:
                self.logger.warning(f"No [tool.py-indexer] section in {config_file}, using defaults")
                self._config = self.DEFAULTS.copy()
        
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}", exc_info=True)
            self._config = self.DEFAULTS.copy()
    
    def _validate_config(self, raw_config: dict) -> dict:
        """
        Validate configuration values.
        
        Parameters
        ----------
        raw_config : dict
            Raw configuration from file
            
        Returns
        -------
        dict
            Validated configuration with defaults for invalid values
        """
        validated = {}
        
        for key, default_value in self.DEFAULTS.items():
            value = raw_config.get(key, default_value)
            
            # Validate if rule exists
            if key in self.VALIDATION_RULES:
                validator = self.VALIDATION_RULES[key]
                if not validator(value):
                    self.logger.warning(
                        f"Invalid config value for '{key}': {value}. Using default: {default_value}"
                    )
                    value = default_value
            
            validated[key] = value
        
        return validated
    
    def _find_config_file(self) -> Optional[Path]:
        """
        Find pyproject.toml in current or parent directories.
        
        Returns
        -------
        Path | None
            Path to pyproject.toml or None if not found
        """
        current = Path.cwd()
        
        # Check current directory
        config_file = current / 'pyproject.toml'
        if config_file.exists():
            return config_file
        
        # Check parent directory
        parent = current.parent
        config_file = parent / 'pyproject.toml'
        if config_file.exists():
            return config_file
        
        return None
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Parameters
        ----------
        key : str
            Configuration key
        default : Any, optional
            Default value if key not found
            
        Returns
        -------
        Any
            Configuration value
        """
        return self._config.get(key, self.DEFAULTS.get(key, default))
    
    def __getattr__(self, name: str) -> Any:
        """
        Proxy attribute access to config dict.
        
        Parameters
        ----------
        name : str
            Attribute name
            
        Returns
        -------
        Any
            Configuration value
            
        Raises
        ------
        AttributeError
            If attribute doesn't exist in config
        """
        if name.startswith('_'):
            # Avoid infinite recursion for private attributes
            raise AttributeError(f"Config has no attribute '{name}'")
        
        if name in self.DEFAULTS:
            return self.get(name)
        
        raise AttributeError(f"Config has no attribute '{name}'")


# Global configuration instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Get global configuration instance.
    
    Returns
    -------
    Config
        Configuration instance
        
    Examples
    --------
    >>> config = get_config()
    >>> print(config.max_file_size)
    1048576
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config()
    
    return _config_instance


def reload_config(config_path: Optional[str | Path] = None) -> Config:
    """
    Reload configuration from file.
    
    Parameters
    ----------
    config_path : str | Path, optional
        Path to pyproject.toml
        
    Returns
    -------
    Config
        New configuration instance
        
    Examples
    --------
    >>> config = reload_config("./pyproject.toml")
    >>> print(config.log_level)
    'DEBUG'
    """
    global _config_instance
    _config_instance = Config(config_path)
    return _config_instance
