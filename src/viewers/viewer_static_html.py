#!/usr/bin/env python3
"""
Static HTML Viewer Generator for PY-Indexer v3.1.

Generates single-page HTML viewer with:
- Embedded JSON data (INDEX, LOCATION, DOCSTRINGS, COMMENTS)
- Search and filter UI
- Tree navigation
- Detail panels
- Dark/Light mode toggle
- Responsive design

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

import json
from pathlib import Path
from typing import Optional

from utils.utils_logger import get_logger

logger = get_logger(__name__)


class StaticHTMLViewer:
    """
    Generate static HTML viewer for PY-Indexer v3.1.
    
    Creates self-contained HTML file with embedded JSON data
    and interactive JavaScript UI.
    """

    def __init__(self, output_path: Path):
        """
        Initialize HTML viewer generator.

        Parameters
        ----------
        output_path : Path
            Directory where HTML file will be created
        """
        self.logger = get_logger(__name__)
        self.output_path = Path(output_path)
        self.template_path = Path(__file__).parent / 'template_static_html.html'

    def generate(
        self,
        index_data: dict,
        location_data: dict,
        docstrings_data: dict,
        comments_data: dict
    ) -> Path:
        """
        Generate index.html with embedded JSON data.

        Parameters
        ----------
        index_data : dict
            TECH-INDEX data structure
        location_data : dict
            TECH-LOCATION data structure
        docstrings_data : dict
            TECH-DOCSTRINGS data structure
        comments_data : dict
            TECH-COMMENTS data structure

        Returns
        -------
        Path
            Path to generated index.html file

        Raises
        ------
        FileNotFoundError
            If template file not found
        """
        self.logger.info("Generating static HTML viewer...")

        # Load template
        if not self.template_path.exists():
            self.logger.error(f"Template not found: {self.template_path}")
            raise FileNotFoundError(f"Template not found: {self.template_path}")

        with open(self.template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # Escape and embed JSON data
        html_content = self._embed_json_data(
            template,
            index_data,
            location_data,
            docstrings_data,
            comments_data
        )

        # Write output
        output_file = self.output_path / 'index.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        file_size = output_file.stat().st_size
        size_mb = file_size / (1024 * 1024)
        self.logger.info(
            f"Generated HTML viewer: {output_file} ({size_mb:.2f} MB)"
        )

        return output_file

    def _embed_json_data(
        self,
        template: str,
        index_data: dict,
        location_data: dict,
        docstrings_data: dict,
        comments_data: dict
    ) -> str:
        """
        Embed JSON data into HTML template.

        Parameters
        ----------
        template : str
            HTML template content
        index_data : dict
            TECH-INDEX data
        location_data : dict
            TECH-LOCATION data
        docstrings_data : dict
            TECH-DOCSTRINGS data
        comments_data : dict
            TECH-COMMENTS data

        Returns
        -------
        str
            HTML with embedded JSON data
        """
        # Convert to JSON strings (compact, no indent)
        index_json = json.dumps(index_data, ensure_ascii=False)
        location_json = json.dumps(location_data, ensure_ascii=False)
        docstrings_json = json.dumps(docstrings_data, ensure_ascii=False)
        comments_json = json.dumps(comments_data, ensure_ascii=False)

        # Replace placeholders
        html = template.replace('{{INDEX_DATA}}', index_json)
        html = html.replace('{{LOCATION_DATA}}', location_json)
        html = html.replace('{{DOCSTRINGS_DATA}}', docstrings_json)
        html = html.replace('{{COMMENTS_DATA}}', comments_json)

        return html

    def get_statistics(self) -> dict:
        """
        Get viewer generation statistics.

        Returns
        -------
        dict
            Statistics about generated viewer
        """
        return {
            "template_path": str(self.template_path),
            "output_path": str(self.output_path),
            "template_exists": self.template_path.exists()
        }
