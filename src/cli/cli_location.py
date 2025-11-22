#!/usr/bin/env python3
"""
CLI for TECH-LOCATION generation - PY-Indexer v3.0.

Command-line interface for generating TECH-LOCATION from TECH-INDEX.

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

import argparse
import sys
from pathlib import Path

from validator import InputValidator
from builders.builder_location import LocationBuilder
from serializers.serializer_json import JSONSerializer
from utils.utils_logger import get_logger, configure_root_logger

logger = get_logger(__name__)


class LocationCLI:
    """
    CLI for TECH-LOCATION generation.
    
    Handles command-line arguments and orchestrates TECH-LOCATION building.
    """
    
    def __init__(self):
        """Initialize CLI."""
        self.logger = get_logger(__name__)
        self.validator = InputValidator()
    
    def run(self, args: list[str]) -> int:
        """
        Run TECH-LOCATION generation.
        
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
        
        self.logger.info("Starting TECH-LOCATION generation")
        
        try:
            # Validate inputs
            if not self.validator.validate_tech_index_path(parsed_args.tech_index_path):
                print(f"ERROR: Invalid TECH-INDEX path: {parsed_args.tech_index_path}")
                return 1
            
            if not self.validator.validate_output_path(parsed_args.output_path):
                print(f"ERROR: Invalid output path: {parsed_args.output_path}")
                return 1
            
            # Load TECH-INDEX
            print(f"\nLoading TECH-INDEX: {parsed_args.tech_index_path}")
            serializer = JSONSerializer()
            tech_index = serializer.deserialize(parsed_args.tech_index_path)
            
            # Validate TECH-INDEX structure
            if 'meta' not in tech_index:
                print("ERROR: Invalid TECH-INDEX - missing metadata")
                return 1
            
            meta = tech_index.get('meta', {})
            version = meta.get('version', 'unknown')
            project = meta.get('project', 'unknown')
            
            print(f"  Version: {version}")
            print(f"  Project: {project}")
            
            # Build TECH-LOCATION
            print("\nBuilding TECH-LOCATION...")
            builder = LocationBuilder(tech_index, project_name=project)
            tech_location = builder.build()
            
            # Serialize to file
            print(f"\nSerializing to JSON format...")
            output_file = self._get_output_filename(
                parsed_args.output_path,
                "tech-location"
            )
            
            output_serializer = JSONSerializer(minify=False, compress=False)
            output_serializer.serialize(tech_location, output_file)
            
            print(f"\n✓ TECH-LOCATION saved to: {output_file}")
            
            # Display file size
            file_size = Path(output_file).stat().st_size
            print(f"  File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
            
            self.logger.info("TECH-LOCATION generation completed successfully")
            return 0
            
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            self.logger.warning("Process interrupted by user")
            return 1
        except Exception as e:
            print(f"\nERROR: {e}")
            self.logger.error(f"TECH-LOCATION generation failed: {e}", exc_info=True)
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
            description='Generate TECH-LOCATION from TECH-INDEX',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Generate TECH-LOCATION from TECH-INDEX
  python main.py location ./output ./output/tech-index.json

  # From GZIP compressed TECH-INDEX
  python main.py location ./output ./output/tech-index.json.gz
            """
        )
        
        parser.add_argument(
            'output_path',
            help='Path to output directory'
        )
        
        parser.add_argument(
            'tech_index_path',
            help='Path to TECH-INDEX file (JSON or JSON.gz)'
        )
        
        return parser.parse_args(args)
    
    def _get_output_filename(self, output_path: str, base_name: str) -> Path:
        """
        Get output filename.
        
        Parameters
        ----------
        output_path : str
            Output directory path
        base_name : str
            Base filename without extension
            
        Returns
        -------
        Path
            Full output file path
        """
        output_dir = Path(output_path)
        return output_dir / f"{base_name}.json"


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
    cli = LocationCLI()
    return cli.run(args)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
