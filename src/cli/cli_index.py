#!/usr/bin/env python3
"""
CLI for TECH-INDEX generation - PY-Indexer v3.0.

Command-line interface for generating TECH-INDEX from Python projects.

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

import argparse
import sys
from pathlib import Path

from validator import InputValidator
from parser import ASTParser
from indexer import CodeIndexer
from builders.builder_tech_index import TechIndexBuilder
from serializers.serializer_json import JSONSerializer
from serializers.serializer_msgpack import MessagePackSerializer
from utils.utils_logger import get_logger, configure_root_logger
from utils.utils_file import find_python_files

logger = get_logger(__name__)


class IndexCLI:
    """
    CLI for TECH-INDEX generation.
    
    Handles command-line arguments and orchestrates the indexing process.
    """
    
    def __init__(self):
        """Initialize CLI."""
        self.logger = get_logger(__name__)
        self.validator = InputValidator()
    
    def run(self, args: list[str]) -> int:
        """
        Run TECH-INDEX generation.
        
        Parameters
        ----------
        args : list[str]
            Command-line arguments
            
        Returns
        -------
        int
            Exit code (0 = success, 1 = error)
        """
        # Parse arguments
        parsed_args = self.parse_arguments(args)
        
        # Configure logging
        configure_root_logger("main.log")
        
        self.logger.info("Starting TECH-INDEX generation")
        
        try:
            # Validate inputs
            if not self.validator.validate_project_path(parsed_args.project_path):
                print(f"ERROR: Invalid project path: {parsed_args.project_path}")
                return 1
            
            if not self.validator.validate_output_path(parsed_args.output_path):
                print(f"ERROR: Invalid output path: {parsed_args.output_path}")
                return 1
            
            if not self.validator.validate_format(parsed_args.format):
                print(f"ERROR: Invalid format: {parsed_args.format}")
                return 1
            
            if not self.validator.validate_hash_length(parsed_args.hash_len):
                print(f"ERROR: Invalid hash length: {parsed_args.hash_len}")
                return 1
            
            # Find Python files
            print(f"\nScanning project: {parsed_args.project_path}")
            python_files = find_python_files(parsed_args.project_path, recursive=True)
            print(f"Found {len(python_files)} Python files")
            
            if not python_files:
                print("ERROR: No Python files found")
                return 1
            
            # Parse files
            print("\nParsing files...")
            parser = ASTParser()
            parsed_files = []
            
            for i, file_path in enumerate(python_files, 1):
                print(f"  [{i}/{len(python_files)}] {file_path.name}", end='\r')
                parsed = parser.parse_file(file_path)
                if parsed:
                    parsed_files.append(parsed)
            
            print(f"\nSuccessfully parsed {len(parsed_files)} files")
            
            # Index files
            print("\nIndexing...")
            indexer = CodeIndexer(hash_length=parsed_args.hash_len)
            indexer.index_parsed_files(parsed_files)
            
            # Display statistics
            stats = indexer.get_statistics()
            print(f"\nIndexing complete:")
            print(f"  - Names: {stats['total_names']}")
            print(f"  - Files: {stats['total_files']}")
            print(f"  - Defaults: {stats['total_defaults']}")
            print(f"  - Mutable defaults found: {stats['mutable_defaults_count']}")
            print(f"  - SQL queries found: {stats['sql_injections_count']}")
            print(f"  - Hardcoded secrets found: {stats['hardcoded_secrets_count']}")
            
            # Build TECH-INDEX
            print("\nBuilding TECH-INDEX...")
            project_name = Path(parsed_args.project_path).name
            builder = TechIndexBuilder(
                indexer=indexer,
                project_name=project_name,
                compress_names=parsed_args.compress_names,
                hash_length=parsed_args.hash_len
            )
            tech_index = builder.build(parsed_files)
            
            # Serialize to file
            print(f"\nSerializing to {parsed_args.format} format...")
            output_file = self._get_output_filename(
                parsed_args.output_path,
                "tech-index",
                parsed_args.format
            )
            
            serializer = self._get_serializer(parsed_args.format, parsed_args.minify)
            serializer.serialize(tech_index, output_file)
            
            print(f"\n✓ TECH-INDEX saved to: {output_file}")
            
            # Display file size
            file_size = Path(output_file).stat().st_size
            print(f"  File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
            
            self.logger.info("TECH-INDEX generation completed successfully")
            return 0
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            self.logger.warning("Process interrupted by user")
            return 1
        except Exception as e:
            print(f"\nERROR: {e}")
            self.logger.error(f"TECH-INDEX generation failed: {e}", exc_info=True)
            return 1
    
    def parse_arguments(self, args: list[str]) -> argparse.Namespace:
        """
        Parse command-line arguments.
        
        Parameters
        ----------
        args : list[str]
            Command-line arguments
            
        Returns
        -------
        argparse.Namespace
            Parsed arguments
        """
        parser = argparse.ArgumentParser(
            description='Generate TECH-INDEX from Python project',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Generate JSON index
  python main.py index ./my_project ./output

  # Generate compressed JSON
  python main.py index ./my_project ./output --format=json.gz --minify

  # Generate MessagePack index
  python main.py index ./my_project ./output --format=msgpack

  # Compress names array
  python main.py index ./my_project ./output --compress-names

  # Custom hash length
  python main.py index ./my_project ./output --hash-len=32
            """
        )
        
        parser.add_argument(
            'project_path',
            help='Path to Python project directory'
        )
        
        parser.add_argument(
            'output_path',
            help='Path to output directory'
        )
        
        parser.add_argument(
            '--format',
            choices=['json', 'json.gz', 'msgpack'],
            default='json',
            help='Output format (default: json)'
        )
        
        parser.add_argument(
            '--minify',
            action='store_true',
            help='Minify JSON output (no whitespace)'
        )
        
        parser.add_argument(
            '--compress-names',
            action='store_true',
            help='Compress names array with GZIP+Base64'
        )
        
        parser.add_argument(
            '--hash-len',
            type=int,
            choices=[8, 16, 32, 64],
            default=16,
            help='Hash length in characters (default: 16)'
        )
        
        return parser.parse_args(args)
    
    def _get_output_filename(
        self,
        output_path: str,
        base_name: str,
        format_str: str
    ) -> Path:
        """
        Get output filename with appropriate extension.
        
        Parameters
        ----------
        output_path : str
            Output directory path
        base_name : str
            Base filename without extension
        format_str : str
            Format string (json, json.gz, msgpack)
            
        Returns
        -------
        Path
            Full output file path
        """
        output_dir = Path(output_path)
        
        if format_str == 'json':
            extension = '.json'
        elif format_str == 'json.gz':
            extension = '.json.gz'
        elif format_str == 'msgpack':
            extension = '.msgpack'
        else:
            extension = '.json'
        
        return output_dir / f"{base_name}{extension}"
    
    def _get_serializer(self, format_str: str, minify: bool):
        """
        Get serializer for format.
        
        Parameters
        ----------
        format_str : str
            Format string (json, json.gz, msgpack)
        minify : bool
            Minify JSON output
            
        Returns
        -------
        BaseSerializer
            Serializer instance
        """
        if format_str in ['json', 'json.gz']:
            compress = format_str == 'json.gz'
            return JSONSerializer(minify=minify, compress=compress)
        elif format_str == 'msgpack':
            return MessagePackSerializer()
        else:
            return JSONSerializer(minify=minify)


def main(args: list[str]) -> int:
    """
    Main entry point for CLI.
    
    Parameters
    ----------
    args : list[str]
        Command-line arguments
        
    Returns
    -------
    int
        Exit code
    """
    cli = IndexCLI()
    return cli.run(args)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
