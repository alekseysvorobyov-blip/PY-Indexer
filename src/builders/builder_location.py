#!/usr/bin/env python3
"""
TECH-LOCATION Builder v3.1 for PY-Indexer.

Builds file coordinates mapping (location_id → positions).
ONLY contains line numbers - NO structure, NO names, NO docs.

Architecture v3.1:
- Maps location_id to file positions
- Used for IDE navigation, Go to Definition
- Minimal size, fast lookups

Author: PY-Indexer Development Team  
Date: 2025-11-22
"""

from datetime import datetime
from typing import Any

from utils.utils_logger import get_logger

logger = get_logger(__name__)


class LocationBuilder:
    """
    Builds TECH-LOCATION v3.1 structure.
    
    Responsibilities:
    - Map location_id → (file, line_start, line_end)
    - ONLY coordinates, nothing else
    
    Does NOT include:
    - Names (→ INDEX)
    - Structure (→ INDEX)
    - Docstrings (→ DOCSTRINGS)
    - Comments (→ COMMENTS)
    """
    
    def __init__(self, project_name: str = ""):
        """
        Initialize builder.
        
        Parameters
        ----------
        project_name : str, optional
            Project name for metadata
        """
        self.logger = get_logger(__name__)
        self.project_name = project_name
        
        # File paths (same as INDEX)
        self.files = []
        self._file_to_idx = {}
        
        # Coordinate data (by location_id)
        self.modules = []
        self.classes = []
        self.functions = []
        self.imports = []
    
    def add_file(self, file_path: str) -> int:
        """
        Add file to registry (with deduplication).
        
        Parameters
        ----------
        file_path : str
            Relative file path
            
        Returns
        -------
        int
            File index
        """
        if file_path in self._file_to_idx:
            return self._file_to_idx[file_path]
        
        idx = len(self.files)
        self.files.append(file_path)
        self._file_to_idx[file_path] = idx
        return idx
    
    def add_module_location(
        self,
        location_id: int,
        file_path: str,
        line_start: int,
        line_end: int
    ) -> None:
        """
        Add module coordinates.
        
        Parameters
        ----------
        location_id : int
            Location ID from INDEX
        file_path : str
            File path
        line_start : int
            Start line number
        line_end : int
            End line number
        """
        file_idx = self.add_file(file_path)
        self.modules.append([location_id, file_idx, line_start, line_end])
        
        self.logger.debug(f"Added module location: location_id={location_id}, lines {line_start}-{line_end}")
    
    def add_class_location(
        self,
        location_id: int,
        file_path: str,
        line_start: int,
        line_end: int
    ) -> None:
        """
        Add class coordinates.
        
        Parameters
        ----------
        location_id : int
            Location ID from INDEX
        file_path : str
            File path
        line_start : int
            Start line number
        line_end : int
            End line number
        """
        file_idx = self.add_file(file_path)
        self.classes.append([location_id, file_idx, line_start, line_end])
        
        self.logger.debug(f"Added class location: location_id={location_id}, lines {line_start}-{line_end}")
    
    def add_function_location(
        self,
        location_id: int,
        file_path: str,
        line_start: int,
        line_end: int
    ) -> None:
        """
        Add function coordinates.
        
        Parameters
        ----------
        location_id : int
            Location ID from INDEX
        file_path : str
            File path
        line_start : int
            Start line number
        line_end : int
            End line number
        """
        file_idx = self.add_file(file_path)
        self.functions.append([location_id, file_idx, line_start, line_end])
        
        self.logger.debug(f"Added function location: location_id={location_id}, lines {line_start}-{line_end}")
    
    def add_import_location(
        self,
        location_id: int,
        file_path: str,
        line_number: int
    ) -> None:
        """
        Add import coordinates.
        
        Parameters
        ----------
        location_id : int
            Location ID from INDEX
        file_path : str
            File path
        line_number : int
            Line number where import occurs
        """
        file_idx = self.add_file(file_path)
        self.imports.append([location_id, file_idx, line_number])
        
        self.logger.debug(f"Added import location: location_id={location_id}, line {line_number}")
    
    def build(self) -> dict[str, Any]:
        """
        Build final TECH-LOCATION structure.
        
        Returns
        -------
        dict
            TECH-LOCATION v3.1 structure
        """
        location = {
            "meta": {
                "version": "3.1",
                "generated": datetime.utcnow().isoformat() + "Z",
                "project": self.project_name
            },
            "files": self.files,
            "modules": self.modules,
            "classes": self.classes,
            "functions": self.functions,
            "imports": self.imports
        }
        
        self.logger.info(
            f"Built TECH-LOCATION: {len(self.classes)} classes, "
            f"{len(self.functions)} functions with coordinates"
        )
        
        return location
    
    def get_statistics(self) -> dict[str, int]:
        """
        Get location statistics.
        
        Returns
        -------
        dict
            Statistics dictionary
        """
        return {
            "files": len(self.files),
            "modules": len(self.modules),
            "classes": len(self.classes),
            "functions": len(self.functions),
            "imports": len(self.imports)
        }
