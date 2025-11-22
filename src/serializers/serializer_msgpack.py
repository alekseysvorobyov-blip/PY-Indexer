#!/usr/bin/env python3
"""
MessagePack Serializer for PY-Indexer v3.0.

Provides MessagePack serialization:
- Binary compact format
- Faster than JSON
- Smaller file sizes
- Requires msgpack module

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

from pathlib import Path

from serializers.serializer_base import BaseSerializer
from utils.utils_logger import get_logger

logger = get_logger(__name__)


class MessagePackSerializer(BaseSerializer):
    """
    MessagePack serializer for TECH-INDEX and TECH-LOCATION.
    
    Provides compact binary serialization format.
    Requires msgpack module to be installed.
    """
    
    def __init__(self):
        """
        Initialize MessagePack serializer.
        
        Raises
        ------
        ImportError
            If msgpack module is not installed
        """
        super().__init__()
        
        try:
            import msgpack
            self.msgpack = msgpack
            self.logger.debug("msgpack module loaded successfully")
        except ImportError:
            self.logger.error("msgpack module not installed")
            raise ImportError(
                "msgpack module is required for MessagePack serialization. "
                "Install with: pip install msgpack"
            )
    
    def serialize(self, data: dict, output_path: str | Path) -> None:
        """
        Serialize data to MessagePack file.
        
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
        >>> serializer = MessagePackSerializer()
        >>> serializer.serialize({"key": "value"}, "output.msgpack")
        """
        path = Path(output_path)
        
        try:
            # Serialize to MessagePack bytes
            packed = self.msgpack.packb(data, use_bin_type=True)
            
            # Write to file
            with open(path, 'wb') as f:
                f.write(packed)
            
            self.logger.info(f"Serialized (MessagePack) to {path}")
            
            # Log file size
            file_size = path.stat().st_size
            self.logger.debug(f"Output file size: {file_size} bytes")
            
        except IOError as e:
            self.logger.error(f"Cannot write to {path}: {e}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"MessagePack serialization error: {e}", exc_info=True)
            raise
    
    def deserialize(self, input_path: str | Path) -> dict:
        """
        Deserialize data from MessagePack file.
        
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
            If MessagePack data is invalid
            
        Examples
        --------
        >>> serializer = MessagePackSerializer()
        >>> data = serializer.deserialize("input.msgpack")
        >>> print(data.keys())
        dict_keys(['meta', 'names', 'files'])
        """
        path = Path(input_path)
        
        if not path.exists():
            self.logger.error(f"File not found: {path}")
            raise FileNotFoundError(f"File not found: {path}")
        
        try:
            # Read MessagePack file
            with open(path, 'rb') as f:
                packed = f.read()
            
            # Deserialize from MessagePack bytes
            data = self.msgpack.unpackb(packed, raw=False)
            
            self.logger.info(f"Deserialized (MessagePack) from {path}")
            return data
            
        except self.msgpack.exceptions.ExtraData as e:
            self.logger.error(f"Invalid MessagePack data in {path}: {e}", exc_info=True)
            raise ValueError(f"Invalid MessagePack data in {path}: {e}")
        except IOError as e:
            self.logger.error(f"Cannot read {path}: {e}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"MessagePack deserialization error: {e}", exc_info=True)
            raise
    
    def get_file_extension(self) -> str:
        """
        Get file extension for this serializer.
        
        Returns
        -------
        str
            File extension
        """
        return '.msgpack'
    
    def get_format_name(self) -> str:
        """
        Get format name for this serializer.
        
        Returns
        -------
        str
            Format name
        """
        return 'MessagePack (binary)'
