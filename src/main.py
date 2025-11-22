#!/usr/bin/env python3
"""
PY-Indexer v3.0 - Main Entry Point

Compact Python project indexer for AI analysis.

Commands:
  index     - Generate TECH-INDEX from project
  location  - Generate TECH-LOCATION from TECH-INDEX
  view      - View index contents

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

import sys
from pathlib import Path

from cli.cli_index import main as index_main
from cli.cli_location import main as location_main
from viewers.viewer_index import IndexViewer
from utils.utils_logger import configure_root_logger


def print_usage():
    """Print usage information."""
    print("""
PY-Indexer v3.0 - Compact Python Project Indexer

Usage:
  python main.py <command> [arguments]

Commands:
  index <project_path> <output_path> [options]
      Generate TECH-INDEX from Python project
      
      Options:
        --format=json|json.gz|msgpack    Output format (default: json)
        --minify                         Minify JSON output
        --compress-names                 Compress names array
        --hash-len=8|16|32|64           Hash length (default: 16)
      
      Examples:
        python main.py index ./my_project ./output
        python main.py index ./my_project ./output --format=json.gz --minify
        python main.py index ./my_project ./output --format=msgpack

  location <output_path> <tech_index_path>
      Generate TECH-LOCATION from TECH-INDEX
      
      Examples:
        python main.py location ./output ./output/tech-index.json
        python main.py location ./output ./output/tech-index.json.gz

  view <index_path> [--filter=type] [--no-stats]
      View index contents in human-readable format
      
      Options:
        --filter=functions|classes|modules|imports
        --no-stats                       Hide statistics
      
      Examples:
        python main.py view ./output/tech-index.json
        python main.py view ./output/tech-index.json --filter=functions
        python main.py view ./output/tech-location.json --no-stats

For more information, see README.md
    """)


def main():
    """Main entry point."""
    # Configure logging
    configure_root_logger("main.log")
    
    # Check arguments
    if len(sys.argv) < 2:
        print_usage()
        return 1
    
    command = sys.argv[1].lower()
    
    if command == 'index':
        # Generate TECH-INDEX
        if len(sys.argv) < 4:
            print("ERROR: Missing arguments for 'index' command")
            print("\nUsage: python main.py index <project_path> <output_path> [options]")
            return 1
        
        return index_main(sys.argv[2:])
    
    elif command == 'location':
        # Generate TECH-LOCATION
        if len(sys.argv) < 4:
            print("ERROR: Missing arguments for 'location' command")
            print("\nUsage: python main.py location <output_path> <tech_index_path>")
            return 1
        
        return location_main(sys.argv[2:])
    
    elif command == 'view':
        # View index
        if len(sys.argv) < 3:
            print("ERROR: Missing arguments for 'view' command")
            print("\nUsage: python main.py view <index_path> [--filter=type] [--no-stats]")
            return 1
        
        index_path = sys.argv[2]
        
        # Parse options
        filter_type = None
        show_stats = True
        
        for arg in sys.argv[3:]:
            if arg.startswith('--filter='):
                filter_type = arg.split('=', 1)[1]
            elif arg == '--no-stats':
                show_stats = False
        
        # View index
        viewer = IndexViewer()
        viewer.view(index_path, filter_type=filter_type, show_stats=show_stats)
        return 0
    
    elif command in ['help', '--help', '-h']:
        print_usage()
        return 0
    
    elif command == 'version':
        print("PY-Indexer v3.0")
        return 0
    
    else:
        print(f"ERROR: Unknown command '{command}'")
        print("\nValid commands: index, location, view, help, version")
        print("Run 'python main.py help' for usage information")
        return 1


if __name__ == '__main__':
    sys.exit(main())
