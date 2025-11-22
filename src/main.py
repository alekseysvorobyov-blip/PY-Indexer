#!/usr/bin/env python3
"""
PY-Indexer v3.1 - Main Entry Point.

Generates 4 specialized indexes:
- TECH-INDEX (structure without coordinates)
- TECH-LOCATION (coordinates only)
- TECH-DOCSTRINGS (documentation)
- TECH-COMMENTS (code comments)

Usage:
    python main.py index <project_path> <output_path> [--minified] [--html]
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

    def __init__(self, project_path: str, output_path: str, minified: bool = False, generate_html: bool = False):
        """
        Initialize indexer.

        Parameters
        ----------
        project_path : str
            Path to Python project
        output_path : str
            Path to output directory
        minified : bool, optional
            Generate minified JSON versions (*-mini.json) (default: False)
        generate_html : bool, optional
            Generate interactive HTML viewer (index.html) (default: False)
        """
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.project_path = Path(project_path).resolve()
        self.output_path = Path(output_path).resolve()
        self.minified = minified
        self.generate_html = generate_html

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
        if self.minified:
            self.logger.info("Minified mode enabled (will generate *-mini.json files)")
        if self.generate_html:
            self.logger.info("HTML viewer generation enabled (will create index.html)")

    def index_project(self) -> None:
        """
        Index entire project.

        Generates all 4 index files:
        - tech-index.json
        - tech-location.json
        - tech-docstrings.json
        - tech-comments.json

        If minified=True, also generates:
        - tech-index-mini.json
        - tech-location-mini.json
        - tech-docstrings-mini.json
        - tech-comments-mini.json
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


        # Generate HTML viewer (optional)
        if self.generate_html:
            self._generate_html_viewer()
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

        If minified=True, generates both regular and minified versions.
        """
        self.logger.info("Serializing indexes...")

        # Ensure output directory exists
        ensure_directory(self.output_path)

        # Build indexes
        tech_index = self.index_builder.build()
        tech_location = self.location_builder.build()
        tech_docstrings = self.docstrings_builder.build()
        tech_comments = self.comments_builder.build()

        # Store data for HTML viewer
        self.index_data = tech_index
        self.location_data = tech_location
        self.docstrings_data = tech_docstrings
        self.comments_data = tech_comments

        # Define files and data
        files = [
            ("tech-index.json", tech_index),
            ("tech-location.json", tech_location),
            ("tech-docstrings.json", tech_docstrings),
            ("tech-comments.json", tech_comments)
        ]

        # Write files
        for filename, data in files:
            # Always write regular version (pretty-printed)
            self._write_json_file(filename, data, minify=False)

            # Optionally write minified version
            if self.minified:
                mini_filename = filename.replace('.json', '-mini.json')
                self._write_json_file(mini_filename, data, minify=True)

        # Print statistics
        self._print_statistics()

    def _write_json_file(self, filename: str, data: dict, minify: bool) -> None:
        """
        Write data to JSON file.

        Parameters
        ----------
        filename : str
            Output filename
        data : dict
            Data to serialize
        minify : bool
            If True, write minified JSON (no whitespace)
        """
        output_file = self.output_path / filename

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                if minify:
                    # Minified: no indent, no whitespace
                    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
                else:
                    # Pretty-printed: indent=2
                    json.dump(data, f, indent=2, ensure_ascii=False)

            # Log with file size
            file_size = output_file.stat().st_size
            size_mb = file_size / (1024 * 1024)
            format_type = "minified" if minify else "pretty-printed"

            self.logger.info(
                f"Wrote: {filename} ({format_type}, {size_mb:.2f} MB)"
            )

        except Exception as e:
            self.logger.error(f"Error writing {filename}: {e}", exc_info=True)
            raise

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


    def _generate_html_viewer(self) -> None:
        """
        Generate interactive HTML viewer.

        Creates index.html with embedded JSON data and JavaScript UI.
        """
        self.logger.info("Generating HTML viewer...")

        try:
            from viewers.viewer_static_html import StaticHTMLViewer

            viewer = StaticHTMLViewer(self.output_path)
            html_file = viewer.generate(
                self.index_data,
                self.location_data,
                self.docstrings_data,
                self.comments_data
            )

            self.logger.info(f"HTML viewer created: {html_file}")

        except Exception as e:
            self.logger.error(f"Failed to generate HTML viewer: {e}", exc_info=True)
            raise



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
        logger.exception(f"Error reading {path}: {e}")
        sys.exit(1)


def print_help() -> None:
    """Print help message."""
    print("""
PY-Indexer v3.1 - Python Project Indexer

USAGE:
    python main.py index <project_path> <output_path> [--minified] [--html]
    python main.py view <index_path>
    python main.py help

COMMANDS:
    index       Generate all 4 index files
    view        View index file contents
    help        Show this help message

OPTIONS (for 'index' command):
    --minified  Generate minified JSON versions (*-mini.json)
                Creates both regular and minified files for each index.

EXAMPLES:
    # Index project (regular format)
    python main.py index ./my_project ./output

    # Index project with minified versions
    python main.py index ./my_project ./output --minified

    # View generated index
    python main.py view ./output/tech-index.json

OUTPUT FILES:
    Regular format (always generated):
        tech-index.json         - Code structure (classes, functions, types)
        tech-location.json      - File coordinates (line numbers)
        tech-docstrings.json    - Documentation strings
        tech-comments.json      - Code comments

    Minified format (with --minified flag):
        tech-index-mini.json        - Minified code structure
        tech-location-mini.json     - Minified coordinates
        tech-docstrings-mini.json   - Minified documentation
        tech-comments-mini.json     - Minified comments

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

    parser.add_argument(
        '--minified',
        action='store_true',
        help='Generate minified JSON versions (*-mini.json) [index command only]'
    )

    parser.add_argument(
        '--html',
        action='store_true',
        help='Generate interactive HTML viewer (index.html)'
    )

    args = parser.parse_args()

    try:
        if args.command == 'help':
            print_help()

        elif args.command == 'index':
            if len(args.args) < 2:
                logger.error("Usage: python main.py index <project_path> <output_path> [--minified]")
                sys.exit(1)

            project_path = args.args[0]
            output_path = args.args[1]

            indexer = PyIndexer(project_path, output_path, minified=args.minified, generate_html=args.html)
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
