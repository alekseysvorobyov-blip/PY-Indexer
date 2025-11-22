#!/usr/bin/env python3
"""
TECH-DOCSTRINGS Builder v3.1 for PY-Indexer.

Builds documentation strings index with coordinates.
Links docstrings to code entities via location_id.

Architecture v3.1:
- Text dictionary for deduplication
- Coordinates for each docstring
- Supports multiple docstrings per entity

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

from datetime import datetime
from typing import Any

from utils.utils_logger import get_logger

logger = get_logger(__name__)


class DocstringsBuilder:
    """
    Builds TECH-DOCSTRINGS v3.1 structure.
    
    Responsibilities:
    - Store docstring texts (deduplicated)
    - Link docstrings to entities via location_id
    - Track docstring positions in files
    
    Does NOT include:
    - Code structure (→ INDEX)
    - Type hints (→ INDEX)
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
        
        # Text dictionary
        self.docstrings_text = []
        self._text_to_idx = {}
        
        # File paths
        self.files = []
        self._file_to_idx = {}
        
        # Docstring data (by location_id)
        # Format: [location_id, [[text_idx, file_idx, line_start, line_end], ...]]
        self.modules = []
        self.classes = []
        self.functions = []
        
        # Temporary storage (location_id → list of docstrings)
        self._module_docs = {}
        self._class_docs = {}
        self._function_docs = {}
    
    def add_text(self, text: str) -> int:
        """
        Add docstring text to dictionary (with deduplication).
        
        Parameters
        ----------
        text : str
            Docstring text
            
        Returns
        -------
        int
            Text index
        """
        if text in self._text_to_idx:
            return self._text_to_idx[text]
        
        idx = len(self.docstrings_text)
        self.docstrings_text.append(text)
        self._text_to_idx[text] = idx
        return idx
    
    def add_file(self, file_path: str) -> int:
        """
        Add file to registry (with deduplication).
        
        Parameters
        ----------
        file_path : str
            File path
            
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
    
    def add_module_docstring(
        self,
        location_id: int,
        text: str,
        file_path: str,
        line_start: int,
        line_end: int
    ) -> None:
        """
        Add module docstring.
        
        Parameters
        ----------
        location_id : int
            Module location_id from INDEX
        text : str
            Docstring text
        file_path : str
            File path
        line_start : int
            Start line number
        line_end : int
            End line number
        """
        text_idx = self.add_text(text)
        file_idx = self.add_file(file_path)
        
        if location_id not in self._module_docs:
            self._module_docs[location_id] = []
        
        self._module_docs[location_id].append([text_idx, file_idx, line_start, line_end])
        
        self.logger.debug(f"Added module docstring: location_id={location_id}, lines {line_start}-{line_end}")
    
    def add_class_docstring(
        self,
        location_id: int,
        text: str,
        file_path: str,
        line_start: int,
        line_end: int
    ) -> None:
        """
        Add class docstring.
        
        Parameters
        ----------
        location_id : int
            Class location_id from INDEX
        text : str
            Docstring text
        file_path : str
            File path
        line_start : int
            Start line number
        line_end : int
            End line number
        """
        text_idx = self.add_text(text)
        file_idx = self.add_file(file_path)
        
        if location_id not in self._class_docs:
            self._class_docs[location_id] = []
        
        self._class_docs[location_id].append([text_idx, file_idx, line_start, line_end])
        
        self.logger.debug(f"Added class docstring: location_id={location_id}, lines {line_start}-{line_end}")
    
    def add_function_docstring(
        self,
        location_id: int,
        text: str,
        file_path: str,
        line_start: int,
        line_end: int
    ) -> None:
        """
        Add function docstring.
        
        Parameters
        ----------
        location_id : int
            Function location_id from INDEX
        text : str
            Docstring text
        file_path : str
            File path
        line_start : int
            Start line number
        line_end : int
            End line number
        """
        text_idx = self.add_text(text)
        file_idx = self.add_file(file_path)
        
        if location_id not in self._function_docs:
            self._function_docs[location_id] = []
        
        self._function_docs[location_id].append([text_idx, file_idx, line_start, line_end])
        
        self.logger.debug(f"Added function docstring: location_id={location_id}, lines {line_start}-{line_end}")
    
    def build(self) -> dict[str, Any]:
        """
        Build final TECH-DOCSTRINGS structure.
        
        Returns
        -------
        dict
            TECH-DOCSTRINGS v3.1 structure
        """
        # Convert temp storage to final format
        self.modules = [[loc_id, docs] for loc_id, docs in self._module_docs.items()]
        self.classes = [[loc_id, docs] for loc_id, docs in self._class_docs.items()]
        self.functions = [[loc_id, docs] for loc_id, docs in self._function_docs.items()]
        
        docstrings = {
            "meta": {
                "version": "3.1",
                "generated": datetime.utcnow().isoformat() + "Z",
                "project": self.project_name
            },
            "docstrings_text": self.docstrings_text,
            "modules": self.modules,
            "classes": self.classes,
            "functions": self.functions
        }
        
        total_docs = len(self._module_docs) + len(self._class_docs) + len(self._function_docs)
        
        self.logger.info(
            f"Built TECH-DOCSTRINGS: {len(self.docstrings_text)} unique texts, "
            f"{total_docs} total docstrings"
        )
        
        return docstrings
    
    def get_statistics(self) -> dict[str, int]:
        """
        Get docstrings statistics.
        
        Returns
        -------
        dict
            Statistics dictionary
        """
        return {
            "unique_texts": len(self.docstrings_text),
            "modules": len(self._module_docs),
            "classes": len(self._class_docs),
            "functions": len(self._function_docs),
            "total": len(self._module_docs) + len(self._class_docs) + len(self._function_docs)
        }
