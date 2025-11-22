#!/usr/bin/env python3
"""
PY-Indexer v3.1 - Main Entry Point

Generates 4 specialized indexes:
- TECH-INDEX (structure without coordinates)
- TECH-LOCATION (coordinates only)
- TECH-DOCSTRINGS (documentation)
- TECH-COMMENTS (code comments)

Usage:
    python main.py index <project_path> <output_path>
    python main.py view <index_path>
    python main.py help

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

from config_loader import get_config
from parser import ASTParser
from builders.builder_tech_index import TechIndexBuilder
from builders.builder_location import LocationBuilder
from builders.builder_docstrings import DocstringsBuilder
from builders.builder_comments import CommentsBuilder
from utils.utils_logger import get_logger
from utils.utils_file import find_python_files, ensure_directory

logger = get_logger(__name__)


class PyIndexer:
    """
    Main indexer class for PY-Indexer v3.1.
    
    Coordinates parsing, building, and serialization of all 4 index files.
    """
    
    def __init__(self, project_path: str, output_path: str):
        """
        Initialize indexer.
        
        Parameters
        ----------
        project_path : str
            Path to Python project
        output_path : str
            Path to output directory
        """
        self.logger = get_logger(__name__)
        self.config = get_config()
        
        self.project_path = Path(project_path).resolve()
        self.output_path = Path(output_path).resolve()
        
        if not self.project_path.exists():
            raise FileNotFoundError(f"Project path not found: {self.project_path}")
        
        # Project name
        self.project_name = self.project_path.name
        
        # Initialize components
        self.parser = ASTParser()
        
        # Initialize builders
        self.index_builder = TechIndexBuilder(self.project_name)
        self.location_builder = LocationBuilder(self.project_name)
        self.docstrings_builder = DocstringsBuilder(self.project_name)
        self.comments_builder = CommentsBuilder(self.project_name)
        
        self.logger.info(f"Initialized PyIndexer for project: {self.project_name}")
    
    def index_project(self) -> None:
        """
        Index entire project.
        
        Generates all 4 index files:
        - tech-index.json
        - tech-location.json
        - tech-docstrings.json
        - tech-comments.json
        """
        self.logger.info(f"Starting indexing: {self.project_path}")
        
        # Find Python files
        python_files = find_python_files(self.project_path, recursive=True)
        self.logger.info(f"Found {len(python_files)} Python files")
        
        if not python_files:
            self.logger.warning("No Python files found!")
            return
        
        # Parse all files
        parsed_files = []
        for py_file in python_files:
            try:
                parsed = self.parser.parse_file(py_file)
                if parsed:
                    parsed_files.append(parsed)
            except Exception as e:
                self.logger.error(f"Error parsing {py_file}: {e}", exc_info=True)
                continue
        
        self.logger.info(f"Parsed {len(parsed_files)} files successfully")
        
        # Build indexes
        self._build_indexes(parsed_files)
        
        # Serialize to files
        self._serialize_indexes()
        
        self.logger.info("Indexing complete!")
    
    def _build_indexes(self, parsed_files: list) -> None:
        """
        Build all 4 indexes from parsed files.
        
        Parameters
        ----------
        parsed_files : list
            List of ParsedFile objects
        """
        self.logger.info("Building indexes...")
        
        for parsed_file in parsed_files:
            # Get relative path
            rel_path = str(Path(parsed_file.file_path).relative_to(self.project_path))
            rel_path = rel_path.replace('\\', '/')
            
            # Add module
            module_loc_id = self.index_builder.add_module(
                parsed_file.module_name,
                rel_path
            )
            
            # Add module location (entire file)
            self.location_builder.add_module_location(
                module_loc_id,
                rel_path,
                1,
                parsed_file.line_count
            )
            
            # Add module docstring if exists
            if parsed_file.module_docstring:
                doc_lines = parsed_file.module_docstring.count('\n') + 1
                self.docstrings_builder.add_module_docstring(
                    module_loc_id,
                    parsed_file.module_docstring,
                    rel_path,
                    1,
                    min(doc_lines + 1, 10)
                )
            
            # Add classes
            for class_info in parsed_file.classes:
                class_loc_id = self.index_builder.add_class(
                    class_info.name,
                    class_info.bases,
                    rel_path
                )
                
                # Add class location
                self.location_builder.add_class_location(
                    class_loc_id,
                    rel_path,
                    class_info.line_start,
                    class_info.line_end
                )
                
                # Add class docstring
                if class_info.docstring:
                    doc_lines = class_info.docstring.count('\n') + 1
                    self.docstrings_builder.add_class_docstring(
                        class_loc_id,
                        class_info.docstring,
                        rel_path,
                        class_info.line_start + 1,
                        class_info.line_start + min(doc_lines + 1, 10)
                    )
                
                # Add class decorators
                if class_info.decorators:
                    self.index_builder.add_decorators(class_loc_id, class_info.decorators)
                
                # Add methods
                for method in class_info.methods:
                    # Find parent class index
                    parent_idx = len(self.index_builder.classes) - 1
                    
                    method_loc_id = self.index_builder.add_function(
                        method.name,
                        parent_idx,
                        rel_path
                    )
                    
                    # Add method location
                    self.location_builder.add_function_location(
                        method_loc_id,
                        rel_path,
                        method.line_start,
                        method.line_end
                    )
                    
                    # Add method docstring
                    if method.docstring:
                        doc_lines = method.docstring.count('\n') + 1
                        self.docstrings_builder.add_function_docstring(
                            method_loc_id,
                            method.docstring,
                            rel_path,
                            method.line_start + 1,
                            method.line_start + min(doc_lines + 1, 10)
                        )
                    
                    # Add method decorators
                    if method.decorators:
                        self.index_builder.add_decorators(method_loc_id, method.decorators)
                    
                    # Add type hints
                    if method.parameters or method.return_type:
                        params = []
                        for param in method.parameters:
                            if param.type_hint:
                                params.append((param.name, param.type_hint))
                        
                        self.index_builder.add_typehint(
                            method_loc_id,
                            params,
                            method.return_type
                        )
            
            # Add module-level functions
            for func in parsed_file.functions:
                func_loc_id = self.index_builder.add_function(
                    func.name,
                    -1,  # Module-level
                    rel_path
                )
                
                # Add function location
                self.location_builder.add_function_location(
                    func_loc_id,
                    rel_path,
                    func.line_start,
                    func.line_end
                )
                
                # Add function docstring
                if func.docstring:
                    doc_lines = func.docstring.count('\n') + 1
                    self.docstrings_builder.add_function_docstring(
                        func_loc_id,
                        func.docstring,
                        rel_path,
                        func.line_start + 1,
                        func.line_start + min(doc_lines + 1, 10)
                    )
                
                # Add decorators
                if func.decorators:
                    self.index_builder.add_decorators(func_loc_id, func.decorators)
                
                # Add type hints
                if func.parameters or func.return_type:
                    params = []
                    for param in func.parameters:
                        if param.type_hint:
                            params.append((param.name, param.type_hint))
                    
                    self.index_builder.add_typehint(
                        func_loc_id,
                        params,
                        func.return_type
                    )
            
            # Add imports
            for import_info in parsed_file.imports:
                import_loc_id = self.index_builder.add_import(
                    import_info.module,
                    rel_path
                )
                
                # Add import location
                self.location_builder.add_import_location(
                    import_loc_id,
                    rel_path,
                    import_info.line
                )
            
            # Add comments
            for comment in parsed_file.comments:
                # Add to module level
                self.comments_builder.add_module_comment(
                    module_loc_id,
                    comment.text,
                    rel_path,
                    comment.line
                )
        
        self.logger.info("Index building complete")
    
    def _serialize_indexes(self) -> None:
        """
        Serialize all indexes to JSON files.
        """
        self.logger.info("Serializing indexes...")
        
        # Ensure output directory exists
        ensure_directory(self.output_path)
        
        # Build indexes
        tech_index = self.index_builder.build()
        tech_location = self.location_builder.build()
        tech_docstrings = self.docstrings_builder.build()
        tech_comments = self.comments_builder.build()
        
        # Write files
        files = [
            ("tech-index.json", tech_index),
            ("tech-location.json", tech_location),
            ("tech-docstrings.json", tech_docstrings),
            ("tech-comments.json", tech_comments)
        ]
        
        for filename, data in files:
            output_file = self.output_path / filename
            
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"Wrote: {output_file}")
            except Exception as e:
                self.logger.error(f"Error writing {output_file}: {e}", exc_info=True)
                raise
        
        # Print statistics
        self._print_statistics()
    
    def _print_statistics(self) -> None:
        """Print indexing statistics."""
        print("\n" + "="*60)
        print("INDEXING STATISTICS")
        print("="*60)
        
        print("\nTECH-INDEX:")
        stats = self.index_builder.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\nTECH-LOCATION:")
        stats = self.location_builder.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\nTECH-DOCSTRINGS:")
        stats = self.docstrings_builder.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\nTECH-COMMENTS:")
        stats = self.comments_builder.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n" + "="*60)


def view_index(index_path: str) -> None:
    """
    View index file contents.
    
    Parameters
    ----------
    index_path : str
        Path to index JSON file
    """
    path = Path(index_path)
    
    if not path.exists():
        logger.error(f"File not found: {path}")
        sys.exit(1)
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Error reading {path}: {e}", exc_info=True)
        sys.exit(1)


def print_help() -> None:
    """Print help message."""
    print("""
PY-Indexer v3.1 - Python Project Indexer

USAGE:
    python main.py index <project_path> <output_path>
    python main.py view <index_path>
    python main.py help

COMMANDS:
    index   - Generate all 4 index files
    view    - View index file contents
    help    - Show this help message

EXAMPLES:
    # Index project
    python main.py index ./my_project ./output

    # View generated index
    python main.py view ./output/tech-index.json

OUTPUT FILES:
    tech-index.json       - Code structure (classes, functions, types)
    tech-location.json    - File coordinates (line numbers)
    tech-docstrings.json  - Documentation strings
    tech-comments.json    - Code comments

For more information, see README.md
""")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="PY-Indexer v3.1 - Python Project Indexer",
        add_help=False
    )
    
    parser.add_argument(
        'command',
        choices=['index', 'view', 'help'],
        help='Command to execute'
    )
    
    parser.add_argument(
        'args',
        nargs='*',
        help='Command arguments'
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == 'help':
            print_help()
        
        elif args.command == 'index':
            if len(args.args) < 2:
                logger.error("Usage: python main.py index <project_path> <output_path>")
                sys.exit(1)
            
            project_path = args.args[0]
            output_path = args.args[1]
            
            indexer = PyIndexer(project_path, output_path)
            indexer.index_project()
        
        elif args.command == 'view':
            if len(args.args) < 1:
                logger.error("Usage: python main.py view <index_path>")
                sys.exit(1)
            
            index_path = args.args[0]
            view_index(index_path)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
