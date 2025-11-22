#!/usr/bin/env python3
"""
Base Serializer for PY-Indexer v3.0.

Abstract base class for all serializers.
Defines common interface for serialization/deserialization.

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

from abc import ABC, abstractmethod
from pathlib import Path

from utils.utils_logger import get_logger

logger = get_logger(__name__)


class BaseSerializer(ABC):
    """
    Abstract base class for serializers.
    
    All serializers must implement serialize() and deserialize() methods.
    """
    
    def __init__(self):
        """Initialize serializer."""
        self.logger = get_logger(__name__)
    
    @abstractmethod
    def serialize(self, data: dict, output_path: str | Path) -> None:
        """
        Serialize data to file.
        
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
        """
        pass
    
    @abstractmethod
    def deserialize(self, input_path: str | Path) -> dict:
        """
        Deserialize data from file.
        
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
            If file content is invalid
        """
        pass
    
    def get_file_extension(self) -> str:
        """
        Get file extension for this serializer.
        
        Returns
        -------
        str
            File extension (e.g., '.json', '.msgpack')
        """
        return '.dat'
