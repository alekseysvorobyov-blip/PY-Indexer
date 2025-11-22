#!/usr/bin/env python3
"""
Index Viewer for PY-Indexer v3.0.

Provides human-readable viewing of TECH-INDEX and TECH-LOCATION:
- Pretty-printed output to console
- Filtering by type (functions, classes, modules)
- Statistics display
- Color-coded output (optional)

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

from pathlib import Path
from typing import Optional

from serializers.serializer_json import JSONSerializer
from utils.utils_logger import get_logger

logger = get_logger(__name__)


class IndexViewer:
    """
    Viewer for TECH-INDEX and TECH-LOCATION files.
    
    Displays index contents in human-readable format.
    """
    
    def __init__(self):
        """Initialize viewer."""
        self.logger = get_logger(__name__)
        self.serializer = JSONSerializer()
    
    def view(
        self,
        index_path: str | Path,
        filter_type: Optional[str] = None,
        show_stats: bool = True
    ) -> None:
        """
        View index file.
        
        Parameters
        ----------
        index_path : str | Path
            Path to TECH-INDEX or TECH-LOCATION file
        filter_type : str, optional
            Filter by type: 'functions', 'classes', 'modules', 'imports'
        show_stats : bool, optional
            Show statistics at the end (default: True)
        """
        try:
            # Load index
            index = self.serializer.deserialize(index_path)
            
            print(f"\n{'='*80}")
            print(f"Index Viewer - {Path(index_path).name}")
            print(f"{'='*80}\n")
            
            # Display metadata
            self._display_metadata(index)
            
            # Display sections based on filter
            if filter_type is None:
                self._display_all_sections(index)
            elif filter_type == 'functions':
                self._display_functions(index)
            elif filter_type == 'classes':
                self._display_classes(index)
            elif filter_type == 'modules':
                self._display_modules(index)
            elif filter_type == 'imports':
                self._display_imports(index)
            else:
                print(f"Unknown filter type: {filter_type}")
                print("Valid filters: functions, classes, modules, imports")
            
            # Display statistics
            if show_stats:
                self._display_statistics(index)
            
            print(f"\n{'='*80}\n")
            
        except Exception as e:
            self.logger.error(f"Error viewing index: {e}", exc_info=True)
            print(f"ERROR: Cannot view index - {e}")
    
    def _display_metadata(self, index: dict) -> None:
        """Display metadata section."""
        meta = index.get('meta', {})
        
        print("METADATA")
        print("-" * 40)
        print(f"  Version: {meta.get('version', 'unknown')}")
        print(f"  Project: {meta.get('project', 'unknown')}")
        print(f"  Generated: {meta.get('generated', 'unknown')}")
        print()
    
    def _display_all_sections(self, index: dict) -> None:
        """Display all sections."""
        self._display_modules(index)
        self._display_classes(index)
        self._display_functions(index)
        self._display_imports(index)
    
    def _display_modules(self, index: dict) -> None:
        """Display modules section."""
        modules = index.get('modules', [])
        
        if not modules:
            return
        
        print("MODULES")
        print("-" * 40)
        
        names = index.get('names', [])
        files = index.get('files', [])
        
        for i, module in enumerate(modules[:10]):  # Show first 10
            if isinstance(module, list) and len(module) >= 3:
                name_idx, line_start, parent_idx = module[:3]
                name = names[name_idx] if name_idx < len(names) else f"idx:{name_idx}"
                print(f"  [{i}] {name} (line {line_start})")
        
        if len(modules) > 10:
            print(f"  ... and {len(modules) - 10} more modules")
        
        print()
    
    def _display_classes(self, index: dict) -> None:
        """Display classes section."""
        classes = index.get('classes', [])
        
        if not classes:
            return
        
        print("CLASSES")
        print("-" * 40)
        
        names = index.get('names', [])
        files = index.get('files', [])
        
        for i, cls in enumerate(classes[:10]):  # Show first 10
            if isinstance(cls, list) and len(cls) >= 3:
                name_idx, line_start, file_idx = cls[:3]
                name = names[name_idx] if name_idx < len(names) else f"idx:{name_idx}"
                file_path = files[file_idx] if file_idx < len(files) else f"idx:{file_idx}"
                
                # Get base classes if available
                bases = []
                if len(cls) > 3 and isinstance(cls[3], list):
                    for base_idx in cls[3]:
                        base_name = names[base_idx] if base_idx < len(names) else f"idx:{base_idx}"
                        bases.append(base_name)
                
                bases_str = f"({', '.join(bases)})" if bases else ""
                print(f"  [{i}] {name}{bases_str}")
                print(f"      File: {Path(file_path).name} (line {line_start})")
        
        if len(classes) > 10:
            print(f"  ... and {len(classes) - 10} more classes")
        
        print()
    
    def _display_functions(self, index: dict) -> None:
        """Display functions section."""
        functions = index.get('functions', [])
        
        if not functions:
            return
        
        print("FUNCTIONS")
        print("-" * 40)
        
        names = index.get('names', [])
        files = index.get('files', [])
        
        for i, func in enumerate(functions[:10]):  # Show first 10
            if isinstance(func, list) and len(func) >= 3:
                name_idx, line_start, file_idx = func[:3]
                name = names[name_idx] if name_idx < len(names) else f"idx:{name_idx}"
                file_path = files[file_idx] if file_idx < len(files) else f"idx:{file_idx}"
                
                print(f"  [{i}] {name}()")
                print(f"      File: {Path(file_path).name} (line {line_start})")
        
        if len(functions) > 10:
            print(f"  ... and {len(functions) - 10} more functions")
        
        print()
    
    def _display_imports(self, index: dict) -> None:
        """Display imports section."""
        imports = index.get('imports', [])
        
        if not imports:
            return
        
        print("IMPORTS")
        print("-" * 40)
        
        names = index.get('names', [])
        
        # Group imports by module
        import_map = {}
        for imp in imports:
            if isinstance(imp, list) and len(imp) >= 1:
                module_idx = imp[0]
                module_name = names[module_idx] if module_idx < len(names) else f"idx:{module_idx}"
                import_map[module_name] = import_map.get(module_name, 0) + 1
        
        # Display top 10 most imported modules
        sorted_imports = sorted(import_map.items(), key=lambda x: x[1], reverse=True)
        for module, count in sorted_imports[:10]:
            print(f"  {module} (used {count}x)")
        
        if len(sorted_imports) > 10:
            print(f"  ... and {len(sorted_imports) - 10} more imports")
        
        print()
    
    def _display_statistics(self, index: dict) -> None:
        """Display statistics."""
        print("STATISTICS")
        print("-" * 40)
        
        # Count items
        names_count = len(index.get('names', []))
        files_count = len(index.get('files', []))
        modules_count = len(index.get('modules', []))
        classes_count = len(index.get('classes', []))
        functions_count = len(index.get('functions', []))
        imports_count = len(index.get('imports', []))
        
        print(f"  Names: {names_count}")
        print(f"  Files: {files_count}")
        print(f"  Modules: {modules_count}")
        print(f"  Classes: {classes_count}")
        print(f"  Functions: {functions_count}")
        print(f"  Imports: {imports_count}")
        
        # Code quality statistics
        mutable_defaults = len(index.get('defaultissues', []))
        sql_queries = len(index.get('sqlqueries', []))
        hardcoded_secrets = len(index.get('hardcodedsecrets', []))
        
        if mutable_defaults or sql_queries or hardcoded_secrets:
            print()
            print("CODE QUALITY ISSUES")
            print("-" * 40)
            if mutable_defaults:
                print(f"  Mutable defaults: {mutable_defaults}")
            if sql_queries:
                print(f"  SQL queries: {sql_queries}")
            if hardcoded_secrets:
                print(f"  Hardcoded secrets: {hardcoded_secrets}")
