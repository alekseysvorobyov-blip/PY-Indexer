#!/usr/bin/env python3
"""
Input validation for PY-Indexer v3.0.

Provides validation for:
- Project paths
- Output paths
- File formats
- Hash lengths
- Command line arguments

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

from pathlib import Path
from typing import Optional

from utils.utils_logger import get_logger

logger = get_logger(__name__)


class InputValidator:
    """
    Validator for PY-Indexer input parameters.
    
    Validates paths, formats, and other input parameters
    before processing begins.
    """
    
    VALID_FORMATS = ['json', 'json.gz', 'msgpack']
    VALID_HASH_LENGTHS = [8, 16, 32, 64]
    
    def __init__(self):
        """Initialize validator."""
        self.logger = get_logger(__name__)
    
    def validate_project_path(self, path: str) -> bool:
        """
        Validate project directory path.
        
        Checks:
        - Path exists
        - Path is a directory
        - Directory is readable
        - Directory contains at least one .py file
        
        Parameters
        ----------
        path : str
            Project directory path
            
        Returns
        -------
        bool
            True if valid, False otherwise
            
        Examples
        --------
        >>> validator = InputValidator()
        >>> validator.validate_project_path("./src")
        True
        """
        if not path:
            self.logger.error("Project path is empty")
            return False
        
        project_path = Path(path)
        
        # Check existence
        if not project_path.exists():
            self.logger.error(f"Project path does not exist: {path}")
            return False
        
        # Check if directory
        if not project_path.is_dir():
            self.logger.error(f"Project path is not a directory: {path}")
            return False
        
        # Check readability
        if not self._is_readable(project_path):
            self.logger.error(f"Project directory is not readable: {path}")
            return False
        
        # Check for Python files
        py_files = list(project_path.rglob('*.py'))
        if not py_files:
            self.logger.warning(f"No Python files found in project directory: {path}")
            return False
        
        self.logger.info(f"Project path validated: {path} ({len(py_files)} Python files)")
        return True
    
    def validate_output_path(self, path: str, create_if_missing: bool = True) -> bool:
        """
        Validate output directory path.
        
        Checks:
        - Parent directory exists (if path doesn't exist)
        - Path is writable
        - Optionally creates directory
        
        Parameters
        ----------
        path : str
            Output directory path
        create_if_missing : bool, optional
            Create directory if it doesn't exist (default: True)
            
        Returns
        -------
        bool
            True if valid, False otherwise
            
        Examples
        --------
        >>> validator = InputValidator()
        >>> validator.validate_output_path("./output")
        True
        """
        if not path:
            self.logger.error("Output path is empty")
            return False
        
        output_path = Path(path)
        
        # If path exists, check if it's a directory and writable
        if output_path.exists():
            if not output_path.is_dir():
                self.logger.error(f"Output path exists but is not a directory: {path}")
                return False
            
            if not self._is_writable(output_path):
                self.logger.error(f"Output directory is not writable: {path}")
                return False
            
            self.logger.info(f"Output path validated (exists): {path}")
            return True
        
        # Path doesn't exist - check parent
        parent = output_path.parent
        if not parent.exists():
            self.logger.error(f"Parent directory does not exist: {parent}")
            return False
        
        if not self._is_writable(parent):
            self.logger.error(f"Parent directory is not writable: {parent}")
            return False
        
        # Create directory if requested
        if create_if_missing:
            try:
                output_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created output directory: {path}")
            except OSError as e:
                self.logger.error(f"Cannot create output directory {path}: {e}", exc_info=True)
                return False
        
        self.logger.info(f"Output path validated: {path}")
        return True
    
    def validate_format(self, format_str: str) -> bool:
        """
        Validate output format.
        
        Parameters
        ----------
        format_str : str
            Format string: 'json', 'json.gz', or 'msgpack'
            
        Returns
        -------
        bool
            True if valid, False otherwise
            
        Examples
        --------
        >>> validator = InputValidator()
        >>> validator.validate_format("json")
        True
        
        >>> validator.validate_format("xml")
        False
        """
        if not format_str:
            self.logger.error("Format string is empty")
            return False
        
        format_lower = format_str.lower()
        
        if format_lower not in self.VALID_FORMATS:
            self.logger.error(
                f"Invalid format: {format_str}. "
                f"Valid formats: {', '.join(self.VALID_FORMATS)}"
            )
            return False
        
        # Check msgpack availability
        if format_lower == 'msgpack':
            try:
                import msgpack
                self.logger.debug("msgpack module is available")
            except ImportError:
                self.logger.error(
                    "msgpack format requested but msgpack module is not installed. "
                    "Install with: pip install msgpack"
                )
                return False
        
        self.logger.info(f"Format validated: {format_str}")
        return True
    
    def validate_hash_length(self, length: int) -> bool:
        """
        Validate hash length parameter.
        
        Parameters
        ----------
        length : int
            Hash length: 8, 16, 32, or 64
            
        Returns
        -------
        bool
            True if valid, False otherwise
            
        Examples
        --------
        >>> validator = InputValidator()
        >>> validator.validate_hash_length(16)
        True
        
        >>> validator.validate_hash_length(12)
        False
        """
        if length not in self.VALID_HASH_LENGTHS:
            self.logger.error(
                f"Invalid hash length: {length}. "
                f"Valid lengths: {', '.join(map(str, self.VALID_HASH_LENGTHS))}"
            )
            return False
        
        self.logger.info(f"Hash length validated: {length}")
        return True
    
    def validate_file_path(self, path: str, must_exist: bool = True) -> bool:
        """
        Validate file path.
        
        Parameters
        ----------
        path : str
            File path
        must_exist : bool, optional
            File must exist if True (default: True)
            
        Returns
        -------
        bool
            True if valid, False otherwise
            
        Examples
        --------
        >>> validator = InputValidator()
        >>> validator.validate_file_path("tech-index.json")
        True
        """
        if not path:
            self.logger.error("File path is empty")
            return False
        
        file_path = Path(path)
        
        if must_exist:
            if not file_path.exists():
                self.logger.error(f"File does not exist: {path}")
                return False
            
            if not file_path.is_file():
                self.logger.error(f"Path is not a file: {path}")
                return False
            
            if not self._is_readable(file_path):
                self.logger.error(f"File is not readable: {path}")
                return False
        else:
            # Check parent directory
            parent = file_path.parent
            if not parent.exists():
                self.logger.error(f"Parent directory does not exist: {parent}")
                return False
            
            if not self._is_writable(parent):
                self.logger.error(f"Parent directory is not writable: {parent}")
                return False
        
        self.logger.info(f"File path validated: {path}")
        return True
    
    def validate_tech_index_path(self, path: str) -> bool:
        """
        Validate TECH-INDEX file path.
        
        Checks file exists and has valid extension (.json or .msgpack).
        
        Parameters
        ----------
        path : str
            TECH-INDEX file path
            
        Returns
        -------
        bool
            True if valid, False otherwise
            
        Examples
        --------
        >>> validator = InputValidator()
        >>> validator.validate_tech_index_path("tech-index.json")
        True
        """
        if not self.validate_file_path(path, must_exist=True):
            return False
        
        file_path = Path(path)
        valid_extensions = ['.json', '.msgpack', '.gz']
        
        if file_path.suffix not in valid_extensions:
            self.logger.error(
                f"Invalid TECH-INDEX file extension: {file_path.suffix}. "
                f"Valid extensions: {', '.join(valid_extensions)}"
            )
            return False
        
        self.logger.info(f"TECH-INDEX path validated: {path}")
        return True
    
    def _is_readable(self, path: Path) -> bool:
        """
        Check if path is readable.
        
        Parameters
        ----------
        path : Path
            Path to check
            
        Returns
        -------
        bool
            True if readable, False otherwise
        """
        try:
            if path.is_file():
                with open(path, 'r'):
                    pass
            elif path.is_dir():
                list(path.iterdir())
            return True
        except (PermissionError, OSError):
            return False
    
    def _is_writable(self, path: Path) -> bool:
        """
        Check if path is writable.
        
        Parameters
        ----------
        path : Path
            Path to check
            
        Returns
        -------
        bool
            True if writable, False otherwise
        """
        try:
            test_file = path / '.write_test'
            test_file.touch()
            test_file.unlink()
            return True
        except (PermissionError, OSError):
            return False
