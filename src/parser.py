#!/usr/bin/env python3
"""
Python AST Parser for PY-Indexer v3.1

Parses Python files and extracts:
- Classes, methods, functions
- Docstrings, comments
- Type hints, decorators
- Imports

Returns structured data compatible with main.py v3.1 builders.

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from utils.utils_logger import get_logger

logger = get_logger(__name__)


@dataclass
class ParameterInfo:
    """Function/method parameter information."""
    name: str
    type_hint: Optional[str] = None
    default: Optional[str] = None


@dataclass
class FunctionInfo:
    """Function or method information."""
    name: str
    line_start: int
    line_end: int
    docstring: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    parameters: list[ParameterInfo] = field(default_factory=list)
    return_type: Optional[str] = None
    is_async: bool = False


@dataclass
class ClassInfo:
    """Class information."""
    name: str
    line_start: int
    line_end: int
    bases: list[str] = field(default_factory=list)
    docstring: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    methods: list[FunctionInfo] = field(default_factory=list)
    attributes: list[str] = field(default_factory=list)


@dataclass
class ImportInfo:
    """Import statement information."""
    module: str
    line: int
    names: list[str] = field(default_factory=list)
    is_from: bool = False


@dataclass
class CommentInfo:
    """Comment information."""
    text: str
    line: int


@dataclass
class ParsedFile:
    """Complete parsed file information."""
    file_path: str
    module_name: str
    module_docstring: Optional[str] = None
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    imports: list[ImportInfo] = field(default_factory=list)
    comments: list[CommentInfo] = field(default_factory=list)
    line_count: int = 0


class ASTParser:
    """
    AST-based Python parser.
    
    Extracts all code entities from Python files.
    """
    
    def __init__(self):
        """Initialize parser."""
        self.logger = get_logger(__name__)
    
    def parse_file(self, file_path: Path | str) -> Optional[ParsedFile]:
        """
        Parse Python file.
        
        Parameters
        ----------
        file_path : Path | str
            Path to Python file
            
        Returns
        -------
        ParsedFile | None
            Parsed file data or None on error
        """
        path = Path(file_path)
        
        if not path.exists():
            self.logger.error(f"File not found: {path}")
            return None
        
        try:
            # Read file
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Count lines
            line_count = source.count('\n') + 1
            
            # Parse AST
            tree = ast.parse(source, filename=str(path))
            
            # Extract module name
            module_name = path.stem
            
            # Extract module docstring
            module_docstring = ast.get_docstring(tree)
            
            # Initialize parsed file
            parsed = ParsedFile(
                file_path=str(path),
                module_name=module_name,
                module_docstring=module_docstring,
                line_count=line_count
            )
            
            # Extract comments
            parsed.comments = self._extract_comments(source)
            
            # Extract imports
            parsed.imports = self._extract_imports(tree)
            
            # Extract classes and functions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Only top-level classes
                    if self._is_top_level(node, tree):
                        class_info = self._extract_class(node)
                        if class_info:
                            parsed.classes.append(class_info)
                
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    # Only top-level functions
                    if self._is_top_level(node, tree):
                        func_info = self._extract_function(node)
                        if func_info:
                            parsed.functions.append(func_info)
            
            self.logger.debug(
                f"Parsed {path}: {len(parsed.classes)} classes, "
                f"{len(parsed.functions)} functions"
            )
            
            return parsed
        
        except SyntaxError as e:
            self.logger.error(f"Syntax error in {path}: {e}", exc_info=True)
            return None
        except Exception as e:
            self.logger.error(f"Error parsing {path}: {e}", exc_info=True)
            return None
    
    def _is_top_level(self, node: ast.AST, tree: ast.Module) -> bool:
        """
        Check if node is top-level (not nested).
        
        Parameters
        ----------
        node : ast.AST
            AST node
        tree : ast.Module
            Module tree
            
        Returns
        -------
        bool
            True if top-level
        """
        return node in tree.body
    
    def _extract_class(self, node: ast.ClassDef) -> Optional[ClassInfo]:
        """
        Extract class information.
        
        Parameters
        ----------
        node : ast.ClassDef
            Class definition node
            
        Returns
        -------
        ClassInfo | None
            Class information
        """
        try:
            # Extract bases
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(self._get_attribute_name(base))
            
            # Extract docstring
            docstring = ast.get_docstring(node)
            
            # Extract decorators
            decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
            
            # Extract methods
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_info = self._extract_function(item)
                    if method_info:
                        methods.append(method_info)
            
            # Line numbers
            line_start = node.lineno
            line_end = node.end_lineno if hasattr(node, 'end_lineno') else line_start
            
            return ClassInfo(
                name=node.name,
                line_start=line_start,
                line_end=line_end,
                bases=bases,
                docstring=docstring,
                decorators=decorators,
                methods=methods
            )
        
        except Exception as e:
            self.logger.error(f"Error extracting class: {e}", exc_info=True)
            return None
    
    def _extract_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> Optional[FunctionInfo]:
        """
        Extract function information.
        
        Parameters
        ----------
        node : ast.FunctionDef | ast.AsyncFunctionDef
            Function definition node
            
        Returns
        -------
        FunctionInfo | None
            Function information
        """
        try:
            # Extract docstring
            docstring = ast.get_docstring(node)
            
            # Extract decorators
            decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
            
            # Extract parameters
            parameters = []
            for arg in node.args.args:
                param = ParameterInfo(
                    name=arg.arg,
                    type_hint=self._get_annotation(arg) if arg.annotation else None
                )
                parameters.append(param)
            
            # Extract return type
            return_type = self._get_annotation(node) if node.returns else None
            
            # Line numbers
            line_start = node.lineno
            line_end = node.end_lineno if hasattr(node, 'end_lineno') else line_start
            
            # Check if async
            is_async = isinstance(node, ast.AsyncFunctionDef)
            
            return FunctionInfo(
                name=node.name,
                line_start=line_start,
                line_end=line_end,
                docstring=docstring,
                decorators=decorators,
                parameters=parameters,
                return_type=return_type,
                is_async=is_async
            )
        
        except Exception as e:
            self.logger.error(f"Error extracting function: {e}", exc_info=True)
            return None
    
    def _extract_imports(self, tree: ast.Module) -> list[ImportInfo]:
        """
        Extract import statements.
        
        Parameters
        ----------
        tree : ast.Module
            Module tree
            
        Returns
        -------
        list[ImportInfo]
            List of imports
        """
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(ImportInfo(
                        module=alias.name,
                        line=node.lineno,
                        names=[alias.name],
                        is_from=False
                    ))
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    names = [alias.name for alias in node.names]
                    imports.append(ImportInfo(
                        module=node.module,
                        line=node.lineno,
                        names=names,
                        is_from=True
                    ))
        
        return imports
    
    def _extract_comments(self, source: str) -> list[CommentInfo]:
        """
        Extract comments from source code.
        
        Parameters
        ----------
        source : str
            Source code
            
        Returns
        -------
        list[CommentInfo]
            List of comments
        """
        comments = []
        
        for line_num, line in enumerate(source.split('\n'), start=1):
            # Find comment
            stripped = line.strip()
            if stripped.startswith('#'):
                # Remove leading # and whitespace
                comment_text = stripped.lstrip('#').strip()
                if comment_text:  # Skip empty comments
                    comments.append(CommentInfo(
                        text=comment_text,
                        line=line_num
                    ))
        
        return comments
    
    def _get_annotation(self, node: ast.arg | ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        """
        Get type annotation as string.
        
        Parameters
        ----------
        node : ast.arg | ast.FunctionDef | ast.AsyncFunctionDef
            Node with annotation
            
        Returns
        -------
        str
            Annotation string
        """
        try:
            if isinstance(node, ast.arg):
                annotation = node.annotation
            else:
                annotation = node.returns
            
            if annotation is None:
                return ""
            
            return ast.unparse(annotation)
        
        except Exception as e:
            self.logger.debug(f"Error unparsing annotation: {e}")
            return ""
    
    def _get_decorator_name(self, node: ast.expr) -> str:
        """
        Get decorator name.
        
        Parameters
        ----------
        node : ast.expr
            Decorator node
            
        Returns
        -------
        str
            Decorator name
        """
        try:
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                return self._get_attribute_name(node)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    return node.func.id
                elif isinstance(node.func, ast.Attribute):
                    return self._get_attribute_name(node.func)
            
            return ast.unparse(node)
        
        except Exception as e:
            self.logger.debug(f"Error getting decorator name: {e}")
            return ""
    
    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """
        Get full attribute name (e.g., 'module.Class').
        
        Parameters
        ----------
        node : ast.Attribute
            Attribute node
            
        Returns
        -------
        str
            Full attribute name
        """
        try:
            parts = []
            current = node
            
            while isinstance(current, ast.Attribute):
                parts.insert(0, current.attr)
                current = current.value
            
            if isinstance(current, ast.Name):
                parts.insert(0, current.id)
            
            return '.'.join(parts)
        
        except Exception as e:
            self.logger.debug(f"Error getting attribute name: {e}")
            return ""
