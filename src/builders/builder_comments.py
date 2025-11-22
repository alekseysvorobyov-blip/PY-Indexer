#!/usr/bin/env python3
"""
TECH-COMMENTS Builder v3.1 for PY-Indexer.

Builds code comments index with coordinates.
Links comments to code entities via location_id.

Architecture v3.1:
- Text dictionary for deduplication
- Line-level coordinates
- Supports multiple comments per entity
- TODO/FIXME/NOTE detection

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

from datetime import datetime
from typing import Any

from utils.utils_logger import get_logger

logger = get_logger(__name__)


class CommentsBuilder:
    """
    Builds TECH-COMMENTS v3.1 structure.
    
    Responsibilities:
    - Store comment texts (deduplicated)
    - Link comments to entities via location_id
    - Track comment positions (line numbers)
    
    Does NOT include:
    - Code structure (→ INDEX)
    - Type hints (→ INDEX)
    - Docstrings (→ DOCSTRINGS)
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
        self.comments_text = []
        self._text_to_idx = {}
        
        # File paths
        self.files = []
        self._file_to_idx = {}
        
        # Comment data (by location_id)
        # Format: [location_id, [[text_idx, file_idx, line_number], ...]]
        self.modules = []
        self.classes = []
        self.functions = []
        
        # Temporary storage (location_id → list of comments)
        self._module_comments = {}
        self._class_comments = {}
        self._function_comments = {}
    
    def add_text(self, text: str) -> int:
        """
        Add comment text to dictionary (with deduplication).
        
        Parameters
        ----------
        text : str
            Comment text (without # prefix)
            
        Returns
        -------
        int
            Text index
        """
        # Normalize: strip leading/trailing whitespace
        normalized = text.strip()
        
        if normalized in self._text_to_idx:
            return self._text_to_idx[normalized]
        
        idx = len(self.comments_text)
        self.comments_text.append(normalized)
        self._text_to_idx[normalized] = idx
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
    
    def add_module_comment(
        self,
        location_id: int,
        text: str,
        file_path: str,
        line_number: int
    ) -> None:
        """
        Add module-level comment.
        
        Parameters
        ----------
        location_id : int
            Module location_id from INDEX
        text : str
            Comment text
        file_path : str
            File path
        line_number : int
            Line number
        """
        text_idx = self.add_text(text)
        file_idx = self.add_file(file_path)
        
        if location_id not in self._module_comments:
            self._module_comments[location_id] = []
        
        self._module_comments[location_id].append([text_idx, file_idx, line_number])
        
        self.logger.debug(f"Added module comment: location_id={location_id}, line {line_number}")
    
    def add_class_comment(
        self,
        location_id: int,
        text: str,
        file_path: str,
        line_number: int
    ) -> None:
        """
        Add class-level comment.
        
        Parameters
        ----------
        location_id : int
            Class location_id from INDEX
        text : str
            Comment text
        file_path : str
            File path
        line_number : int
            Line number
        """
        text_idx = self.add_text(text)
        file_idx = self.add_file(file_path)
        
        if location_id not in self._class_comments:
            self._class_comments[location_id] = []
        
        self._class_comments[location_id].append([text_idx, file_idx, line_number])
        
        self.logger.debug(f"Added class comment: location_id={location_id}, line {line_number}")
    
    def add_function_comment(
        self,
        location_id: int,
        text: str,
        file_path: str,
        line_number: int
    ) -> None:
        """
        Add function-level comment.
        
        Parameters
        ----------
        location_id : int
            Function location_id from INDEX
        text : str
            Comment text
        file_path : str
            File path
        line_number : int
            Line number
        """
        text_idx = self.add_text(text)
        file_idx = self.add_file(file_path)
        
        if location_id not in self._function_comments:
            self._function_comments[location_id] = []
        
        self._function_comments[location_id].append([text_idx, file_idx, line_number])
        
        self.logger.debug(f"Added function comment: location_id={location_id}, line {line_number}")
    
    def build(self) -> dict[str, Any]:
        """
        Build final TECH-COMMENTS structure.
        
        Returns
        -------
        dict
            TECH-COMMENTS v3.1 structure
        """
        # Convert temp storage to final format
        self.modules = [[loc_id, comments] for loc_id, comments in self._module_comments.items()]
        self.classes = [[loc_id, comments] for loc_id, comments in self._class_comments.items()]
        self.functions = [[loc_id, comments] for loc_id, comments in self._function_comments.items()]
        
        comments = {
            "meta": {
                "version": "3.1",
                "generated": datetime.utcnow().isoformat() + "Z",
                "project": self.project_name
            },
            "comments_text": self.comments_text,
            "modules": self.modules,
            "classes": self.classes,
            "functions": self.functions
        }
        
        total_comments = len(self._module_comments) + len(self._class_comments) + len(self._function_comments)
        
        self.logger.info(
            f"Built TECH-COMMENTS: {len(self.comments_text)} unique texts, "
            f"{total_comments} total comments"
        )
        
        return comments
    
    def get_statistics(self) -> dict[str, int]:
        """
        Get comments statistics.
        
        Returns
        -------
        dict
            Statistics dictionary
        """
        # Count TODO/FIXME/NOTE markers
        todos = sum(1 for text in self.comments_text if 'TODO' in text.upper())
        fixmes = sum(1 for text in self.comments_text if 'FIXME' in text.upper())
        notes = sum(1 for text in self.comments_text if 'NOTE' in text.upper())
        
        return {
            "unique_texts": len(self.comments_text),
            "modules": len(self._module_comments),
            "classes": len(self._class_comments),
            "functions": len(self._function_comments),
            "total": len(self._module_comments) + len(self._class_comments) + len(self._function_comments),
            "todos": todos,
            "fixmes": fixmes,
            "notes": notes
        }
    
    def get_todos(self) -> list[tuple[str, int]]:
        """
        Extract all TODO comments.
        
        Returns
        -------
        list[tuple[str, int]]
            List of (comment_text, text_idx) tuples
        """
        todos = []
        for idx, text in enumerate(self.comments_text):
            if 'TODO' in text.upper():
                todos.append((text, idx))
        return todos
    
    def get_fixmes(self) -> list[tuple[str, int]]:
        """
        Extract all FIXME comments.
        
        Returns
        -------
        list[tuple[str, int]]
            List of (comment_text, text_idx) tuples
        """
        fixmes = []
        for idx, text in enumerate(self.comments_text):
            if 'FIXME' in text.upper():
                fixmes.append((text, idx))
        return fixmes
