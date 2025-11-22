#!/usr/bin/env python3
"""
JSON Serializer for PY-Indexer v3.0.

Provides JSON serialization with:
- Standard JSON format
- GZIP compression (optional)
- Minified output (optional)
- UTF-8 encoding

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

import json
import gzip
from pathlib import Path

from serializers.serializer_base import BaseSerializer
from utils.utils_logger import get_logger

logger = get_logger(__name__)


class JSONSerializer(BaseSerializer):
    """
    JSON serializer for TECH-INDEX and TECH-LOCATION.
    
    Supports:
    - Plain JSON (.json)
    - GZIP compressed JSON (.json.gz)
    - Minified or pretty-printed output
    """
    
    def __init__(self, minify: bool = False, compress: bool = False):
        """
        Initialize JSON serializer.
        
        Parameters
        ----------
        minify : bool, optional
            Output minified JSON without whitespace (default: False)
        compress : bool, optional
            Compress output with GZIP (default: False)
        """
        super().__init__()
        self.minify = minify
        self.compress = compress
    
    def serialize(self, data: dict, output_path: str | Path) -> None:
        """
        Serialize data to JSON file.
        
        Parameters
        ----------
        data : dict
            Data structure to serialize
        output_path : str | Path
            Output file path
            
        Raises
        ------
        IOError
            If file cannot be written
            
        Examples
        --------
        >>> serializer = JSONSerializer(minify=False, compress=False)
        >>> serializer.serialize({"key": "value"}, "output.json")
        
        >>> serializer = JSONSerializer(minify=True, compress=True)
        >>> serializer.serialize({"key": "value"}, "output.json.gz")
        """
        path = Path(output_path)
        
        try:
            # Serialize to JSON string
            if self.minify:
                json_str = json.dumps(
                    data,
                    ensure_ascii=False,
                    separators=(',', ':')
                )
            else:
                json_str = json.dumps(
                    data,
                    ensure_ascii=False,
                    indent=2
                )
            
            # Write to file
            if self.compress:
                # GZIP compressed
                with gzip.open(path, 'wt', encoding='utf-8') as f:
                    f.write(json_str)
                self.logger.info(f"Serialized (GZIP) to {path}")
            else:
                # Plain JSON
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(json_str)
                self.logger.info(f"Serialized to {path}")
            
            # Log file size
            file_size = path.stat().st_size
            self.logger.debug(f"Output file size: {file_size} bytes")
            
        except IOError as e:
            self.logger.error(f"Cannot write to {path}: {e}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Serialization error: {e}", exc_info=True)
            raise
    
    def deserialize(self, input_path: str | Path) -> dict:
        """
        Deserialize data from JSON file.
        
        Parameters
        ----------
        input_path : str | Path
            Input file path
            
        Returns
        -------
        dict
            Deserialized data structure
            
        Raises
        ------
        FileNotFoundError
            If file doesn't exist
        IOError
            If file cannot be read
        ValueError
            If JSON is invalid
            
        Examples
        --------
        >>> serializer = JSONSerializer()
        >>> data = serializer.deserialize("input.json")
        >>> print(data.keys())
        dict_keys(['meta', 'names', 'files'])
        
        >>> data = serializer.deserialize("input.json.gz")
        >>> print(data['meta']['version'])
        '3.0'
        """
        path = Path(input_path)
        
        if not path.exists():
            self.logger.error(f"File not found: {path}")
            raise FileNotFoundError(f"File not found: {path}")
        
        try:
            # Detect if file is GZIP compressed
            is_gzip = path.suffix == '.gz' or self._is_gzip_file(path)
            
            if is_gzip:
                # Read GZIP compressed JSON
                with gzip.open(path, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                self.logger.info(f"Deserialized (GZIP) from {path}")
            else:
                # Read plain JSON
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.logger.info(f"Deserialized from {path}")
            
            return data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in {path}: {e}", exc_info=True)
            raise ValueError(f"Invalid JSON in {path}: {e}")
        except IOError as e:
            self.logger.error(f"Cannot read {path}: {e}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"Deserialization error: {e}", exc_info=True)
            raise
    
    def _is_gzip_file(self, path: Path) -> bool:
        """
        Check if file is GZIP compressed by reading magic bytes.
        
        Parameters
        ----------
        path : Path
            File path to check
            
        Returns
        -------
        bool
            True if file is GZIP compressed
        """
        try:
            with open(path, 'rb') as f:
                magic = f.read(2)
                # GZIP magic bytes: 1f 8b
                return magic == b'\x1f\x8b'
        except Exception:
            return False
    
    def get_file_extension(self) -> str:
        """
        Get file extension for this serializer.
        
        Returns
        -------
        str
            File extension
        """
        if self.compress:
            return '.json.gz'
        return '.json'
    
    def get_format_name(self) -> str:
        """
        Get format name for this serializer.
        
        Returns
        -------
        str
            Format name
        """
        if self.compress:
            return 'JSON (GZIP compressed)'
        elif self.minify:
            return 'JSON (minified)'
        return 'JSON'
