#!/usr/bin/env python3
"""
TECH-INDEX Builder v3.1 for PY-Indexer.

Builds compact code structure index WITHOUT coordinates.
Uses location_id for linking with LOCATION/DOCSTRINGS/COMMENTS files.

Architecture v3.1:
- NO line numbers
- NO docstrings  
- NO comments
- ONLY structure: names, classes, functions, types, decorators

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from utils.utils_logger import get_logger

logger = get_logger(__name__)


class TechIndexBuilder:
    """
    Builds TECH-INDEX v3.1 structure.
    
    Responsibilities:
    - Code structure (classes, functions, imports)
    - Type hints and decorators
    - Name deduplication
    - location_id assignment
    
    Does NOT include:
    - Line numbers (→ LOCATION)
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
        
        # Core registries
        self.names = []  # Unified name dictionary
        self.files = []  # File paths
        
        # Lookup maps (for deduplication)
        self._name_to_idx = {}
        self._file_to_idx = {}
        
        # location_id counter
        self.location_counter = 0
        
        # Structure data
        self.modules = []
        self.classes = []
        self.functions = []
        self.imports = []
        self.attributes = []
        
        # Type data (by location_id)
        self.typehints = {}
        self.decorators = {}
    
    def add_name(self, name: str) -> int:
        """
        Add name to dictionary (with deduplication).
        
        Parameters
        ----------
        name : str
            Name to add
            
        Returns
        -------
        int
            Index in names array
        """
        if name in self._name_to_idx:
            return self._name_to_idx[name]
        
        idx = len(self.names)
        self.names.append(name)
        self._name_to_idx[name] = idx
        return idx
    
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
            Index in files array
        """
        # Normalize path (forward slashes)
        normalized = str(Path(file_path)).replace('\\', '/')
        
        if normalized in self._file_to_idx:
            return self._file_to_idx[normalized]
        
        idx = len(self.files)
        self.files.append(normalized)
        self._file_to_idx[normalized] = idx
        return idx
    
    def get_location_id(self) -> int:
        """
        Generate unique location_id.
        
        Returns
        -------
        int
            New unique location_id
        """
        loc_id = self.location_counter
        self.location_counter += 1
        return loc_id
    
    def add_module(self, name: str, file_path: str, parent_idx: int = -1) -> int:
        """
        Add module to index.
        
        Parameters
        ----------
        name : str
            Module name
        file_path : str
            File path
        parent_idx : int, optional
            Parent module index (-1 for top-level)
            
        Returns
        -------
        int
            location_id
        """
        name_idx = self.add_name(name)
        file_idx = self.add_file(file_path)
        location_id = self.get_location_id()
        
        self.modules.append([name_idx, file_idx, parent_idx, location_id])
        
        self.logger.debug(f"Added module: {name} (location_id={location_id})")
        return location_id
    
    def add_class(
        self,
        name: str,
        base_classes: list[str],
        file_path: str
    ) -> int:
        """
        Add class to index.
        
        Parameters
        ----------
        name : str
            Class name
        base_classes : list[str]
            Base class names
        file_path : str
            File path
            
        Returns
        -------
        int
            location_id
        """
        name_idx = self.add_name(name)
        base_idxs = [self.add_name(base) for base in base_classes]
        file_idx = self.add_file(file_path)
        location_id = self.get_location_id()
        
        self.classes.append([name_idx, base_idxs, file_idx, location_id])
        
        self.logger.debug(f"Added class: {name} (location_id={location_id})")
        return location_id
    
    def add_function(
        self,
        name: str,
        parent_class_idx: int,
        file_path: str
    ) -> int:
        """
        Add function to index.
        
        Parameters
        ----------
        name : str
            Function name
        parent_class_idx : int
            Parent class index (-1 for module-level)
        file_path : str
            File path
            
        Returns
        -------
        int
            location_id
        """
        name_idx = self.add_name(name)
        file_idx = self.add_file(file_path)
        location_id = self.get_location_id()
        
        self.functions.append([name_idx, parent_class_idx, file_idx, location_id])
        
        self.logger.debug(f"Added function: {name} (location_id={location_id})")
        return location_id
    
    def add_import(self, module_name: str, file_path: str) -> int:
        """
        Add import to index.
        
        Parameters
        ----------
        module_name : str
            Imported module name
        file_path : str
            File path where import occurs
            
        Returns
        -------
        int
            location_id
        """
        name_idx = self.add_name(module_name)
        file_idx = self.add_file(file_path)
        location_id = self.get_location_id()
        
        self.imports.append([name_idx, file_idx, location_id])
        
        self.logger.debug(f"Added import: {module_name} (location_id={location_id})")
        return location_id
    
    def add_typehint(
        self,
        location_id: int,
        params: list[tuple[str, str]],
        return_type: str | None
    ) -> None:
        """
        Add type hints for function.
        
        Parameters
        ----------
        location_id : int
            Function location_id
        params : list[tuple[str, str]]
            List of (param_name, type_name) tuples
        return_type : str | None
            Return type name
        """
        param_data = []
        for param_name, type_name in params:
            param_idx = self.add_name(param_name)
            type_idx = self.add_name(type_name)
            param_data.append([param_idx, type_idx])
        
        typehint_data = {"params": param_data}
        
        if return_type:
            typehint_data["return"] = self.add_name(return_type)
        
        self.typehints[str(location_id)] = typehint_data
        
        self.logger.debug(f"Added typehints for location_id={location_id}")
    
    def add_decorators(self, location_id: int, decorator_names: list[str]) -> None:
        """
        Add decorators for function/class.
        
        Parameters
        ----------
        location_id : int
            Entity location_id
        decorator_names : list[str]
            Decorator names
        """
        if not decorator_names:
            return
        
        decorator_idxs = [self.add_name(dec) for dec in decorator_names]
        self.decorators[str(location_id)] = decorator_idxs
        
        self.logger.debug(f"Added {len(decorator_names)} decorators for location_id={location_id}")
    
    def add_attribute(
        self,
        name: str,
        parent_class_idx: int,
        type_name: str | None = None
    ) -> None:
        """
        Add class attribute.
        
        Parameters
        ----------
        name : str
            Attribute name
        parent_class_idx : int
            Parent class index
        type_name : str | None, optional
            Type name
        """
        name_idx = self.add_name(name)
        type_idx = self.add_name(type_name) if type_name else -1
        
        self.attributes.append([name_idx, parent_class_idx, type_idx])
        
        self.logger.debug(f"Added attribute: {name}")
    
    def build(self) -> dict[str, Any]:
        """
        Build final TECH-INDEX structure.
        
        Returns
        -------
        dict
            TECH-INDEX v3.1 structure
        """
        index = {
            "meta": {
                "version": "3.1",
                "generated": datetime.utcnow().isoformat() + "Z",
                "project": self.project_name
            },
            "names": self.names,
            "files": self.files,
            "modules": self.modules,
            "classes": self.classes,
            "functions": self.functions,
            "imports": self.imports,
            "attributes": self.attributes,
            "typehints": self.typehints,
            "decorators": self.decorators
        }
        
        self.logger.info(
            f"Built TECH-INDEX: {len(self.names)} names, "
            f"{len(self.classes)} classes, {len(self.functions)} functions"
        )
        
        return index
    
    def get_statistics(self) -> dict[str, int]:
        """
        Get index statistics.
        
        Returns
        -------
        dict
            Statistics dictionary
        """
        return {
            "names": len(self.names),
            "files": len(self.files),
            "modules": len(self.modules),
            "classes": len(self.classes),
            "functions": len(self.functions),
            "imports": len(self.imports),
            "attributes": len(self.attributes),
            "typehints": len(self.typehints),
            "decorators": len(self.decorators),
            "location_ids": self.location_counter
        }
