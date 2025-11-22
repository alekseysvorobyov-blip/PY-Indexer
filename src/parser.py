#!/usr/bin/env python3
"""
AST Parser for PY-Indexer v3.0.

Parses Python files into structured data with config support:
- Modules
- Classes (with inheritance, attributes, methods)
- Functions (with parameters, type hints, defaults)
- Imports (import, from...import)
- Decorators
- Docstrings
- Comments

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from config_loader import get_config
from utils.utils_logger import get_logger
from utils.utils_file import read_python_file

logger = get_logger(__name__)


@dataclass
class Import:
    """Represents an import statement."""
    module: str
    names: list[str]
    aliases: dict[str, str] = field(default_factory=dict)
    level: int = 0  # For relative imports
    line: int = 0


@dataclass
class Parameter:
    """Represents a function parameter."""
    name: str
    type_hint: Optional[str] = None
    default: Optional[str] = None
    kind: str = "positional"  # positional, keyword, *args, **kwargs, positional_only, keyword_only


@dataclass
class TypeHint:
    """Represents type hints for a function."""
    parameters: dict[str, str] = field(default_factory=dict)
    return_type: Optional[str] = None


@dataclass
class FunctionDef:
    """Represents a function or method definition."""
    name: str
    parameters: list[Parameter]
    return_type: Optional[str] = None
    decorators: list[str] = field(default_factory=list)
    docstring: Optional[str] = None
    is_async: bool = False
    is_method: bool = False
    line_start: int = 0
    line_end: int = 0
    parent_class: Optional[str] = None


@dataclass
class ClassAttribute:
    """Represents a class attribute."""
    name: str
    type_hint: Optional[str] = None
    default: Optional[str] = None
    line: int = 0


@dataclass
class ClassDef:
    """Represents a class definition."""
    name: str
    bases: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    docstring: Optional[str] = None
    methods: list[FunctionDef] = field(default_factory=list)
    attributes: list[ClassAttribute] = field(default_factory=list)
    line_start: int = 0
    line_end: int = 0


@dataclass
class Comment:
    """Represents a comment."""
    text: str
    line: int


@dataclass
class ParsedFile:
    """Represents a parsed Python file."""
    file_path: str
    module_name: str
    imports: list[Import] = field(default_factory=list)
    classes: list[ClassDef] = field(default_factory=list)
    functions: list[FunctionDef] = field(default_factory=list)
    module_docstring: Optional[str] = None
    comments: list[Comment] = field(default_factory=list)


class ASTParser:
    """
    Python AST parser for PY-Indexer.
    
    Extracts structured information from Python source files using config settings.
    """
    
    def __init__(self):
        """Initialize parser with config."""
        self.logger = get_logger(__name__)
        self.config = get_config()
    
    def parse_file(self, file_path: str | Path) -> Optional[ParsedFile]:
        """
        Parse Python file into structured data.
        
        Uses max_file_size from config for file size validation.
        
        Parameters
        ----------
        file_path : str | Path
            Path to Python file
            
        Returns
        -------
        ParsedFile | None
            Parsed file data, or None if parsing fails
            
        Examples
        --------
        >>> parser = ASTParser()
        >>> parsed = parser.parse_file("module.py")
        >>> print(len(parsed.functions))
        5
        """
        try:
            # Read file with config max_file_size
            content = read_python_file(file_path, max_size=self.config.max_file_size)
            tree = ast.parse(content, filename=str(file_path))
            
            file_path_obj = Path(file_path)
            module_name = file_path_obj.stem
            
            parsed = ParsedFile(
                file_path=str(file_path),
                module_name=module_name
            )
            
            # Extract module docstring
            parsed.module_docstring = ast.get_docstring(tree)
            
            # Extract imports
            parsed.imports = self.extract_imports(tree)
            
            # Extract classes
            parsed.classes = self.extract_classes(tree)
            
            # Extract module-level functions
            parsed.functions = self.extract_functions(tree)
            
            # Extract comments
            parsed.comments = self.extract_comments(content)
            
            self.logger.info(
                f"Parsed {file_path}: "
                f"{len(parsed.classes)} classes, "
                f"{len(parsed.functions)} functions, "
                f"{len(parsed.imports)} imports"
            )
            
            return parsed
            
        except SyntaxError as e:
            self.logger.error(f"Syntax error in {file_path}: {e}", exc_info=True)
            return None
        except ValueError as e:
            # File too large or encoding error
            self.logger.error(f"File validation error in {file_path}: {e}", exc_info=True)
            return None
        except Exception as e:
            self.logger.error(f"Error parsing {file_path}: {e}", exc_info=True)
            return None
    
    def extract_imports(self, tree: ast.Module) -> list[Import]:
        """
        Extract import statements from AST.
        
        Parameters
        ----------
        tree : ast.Module
            Parsed AST tree
            
        Returns
        -------
        list[Import]
            List of imports
        """
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_obj = Import(
                        module=alias.name,
                        names=[alias.name],
                        aliases={alias.name: alias.asname} if alias.asname else {},
                        line=node.lineno
                    )
                    imports.append(import_obj)
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module if node.module else ''
                names = [alias.name for alias in node.names]
                aliases = {alias.name: alias.asname for alias in node.names if alias.asname}
                
                import_obj = Import(
                    module=module,
                    names=names,
                    aliases=aliases,
                    level=node.level,
                    line=node.lineno
                )
                imports.append(import_obj)
        
        self.logger.debug(f"Extracted {len(imports)} imports")
        return imports
    
    def extract_classes(self, tree: ast.Module) -> list[ClassDef]:
        """
        Extract class definitions from AST.
        
        Parameters
        ----------
        tree : ast.Module
            Parsed AST tree
            
        Returns
        -------
        list[ClassDef]
            List of class definitions
        """
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_def = self._parse_class(node)
                classes.append(class_def)
        
        self.logger.debug(f"Extracted {len(classes)} classes")
        return classes
    
    def _parse_class(self, node: ast.ClassDef) -> ClassDef:
        """Parse single class definition."""
        # Extract base classes
        bases = []
        for base in node.bases:
            base_name = self._get_name_from_node(base)
            if base_name:
                bases.append(base_name)
        
        # Extract decorators
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
        
        # Extract docstring
        docstring = ast.get_docstring(node)
        
        # Extract methods
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method = self._parse_function(item, is_method=True, parent_class=node.name)
                methods.append(method)
        
        # Extract class attributes
        attributes = self._extract_class_attributes(node)
        
        class_def = ClassDef(
            name=node.name,
            bases=bases,
            decorators=decorators,
            docstring=docstring,
            methods=methods,
            attributes=attributes,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno
        )
        
        return class_def
    
    def _extract_class_attributes(self, node: ast.ClassDef) -> list[ClassAttribute]:
        """Extract class-level attributes."""
        attributes = []
        
        for item in node.body:
            if isinstance(item, ast.AnnAssign):
                # Type annotated attribute: x: int = 5
                name = self._get_name_from_node(item.target)
                type_hint = self._get_type_hint(item.annotation)
                default = self._get_default_value(item.value) if item.value else None
                
                if name:
                    attr = ClassAttribute(
                        name=name,
                        type_hint=type_hint,
                        default=default,
                        line=item.lineno
                    )
                    attributes.append(attr)
            
            elif isinstance(item, ast.Assign):
                # Simple attribute: x = 5
                for target in item.targets:
                    name = self._get_name_from_node(target)
                    if name and not name.startswith('_'):  # Skip private
                        default = self._get_default_value(item.value)
                        attr = ClassAttribute(
                            name=name,
                            default=default,
                            line=item.lineno
                        )
                        attributes.append(attr)
        
        return attributes
    
    def extract_functions(self, tree: ast.Module) -> list[FunctionDef]:
        """
        Extract module-level function definitions from AST.
        
        Parameters
        ----------
        tree : ast.Module
            Parsed AST tree
            
        Returns
        -------
        list[FunctionDef]
            List of function definitions
        """
        functions = []
        
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_def = self._parse_function(node, is_method=False)
                functions.append(func_def)
        
        self.logger.debug(f"Extracted {len(functions)} module-level functions")
        return functions
    
    def _parse_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        is_method: bool = False,
        parent_class: Optional[str] = None
    ) -> FunctionDef:
        """Parse single function/method definition."""
        # Extract parameters
        parameters = self._extract_parameters(node.args)
        
        # Extract return type
        return_type = self._get_type_hint(node.returns) if node.returns else None
        
        # Extract decorators
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
        
        # Extract docstring
        docstring = ast.get_docstring(node)
        
        func_def = FunctionDef(
            name=node.name,
            parameters=parameters,
            return_type=return_type,
            decorators=decorators,
            docstring=docstring,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_method=is_method,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            parent_class=parent_class
        )
        
        return func_def
    
    def _extract_parameters(self, args: ast.arguments) -> list[Parameter]:
        """Extract function parameters with type hints and defaults."""
        parameters = []
        
        # Positional-only parameters (Python 3.8+)
        if hasattr(args, 'posonlyargs'):
            for arg in args.posonlyargs:
                param = Parameter(
                    name=arg.arg,
                    type_hint=self._get_type_hint(arg.annotation),
                    kind="positional_only"
                )
                parameters.append(param)
        
        # Regular positional/keyword parameters
        num_defaults = len(args.defaults)
        num_args = len(args.args)
        
        for i, arg in enumerate(args.args):
            default = None
            if i >= (num_args - num_defaults):
                default_idx = i - (num_args - num_defaults)
                default = self._get_default_value(args.defaults[default_idx])
            
            param = Parameter(
                name=arg.arg,
                type_hint=self._get_type_hint(arg.annotation),
                default=default,
                kind="positional"
            )
            parameters.append(param)
        
        # *args parameter
        if args.vararg:
            param = Parameter(
                name=args.vararg.arg,
                type_hint=self._get_type_hint(args.vararg.annotation),
                kind="*args"
            )
            parameters.append(param)
        
        # Keyword-only parameters
        num_kw_defaults = len(args.kw_defaults)
        for i, arg in enumerate(args.kwonlyargs):
            default = None
            if i < num_kw_defaults and args.kw_defaults[i]:
                default = self._get_default_value(args.kw_defaults[i])
            
            param = Parameter(
                name=arg.arg,
                type_hint=self._get_type_hint(arg.annotation),
                default=default,
                kind="keyword_only"
            )
            parameters.append(param)
        
        # **kwargs parameter
        if args.kwarg:
            param = Parameter(
                name=args.kwarg.arg,
                type_hint=self._get_type_hint(args.kwarg.annotation),
                kind="**kwargs"
            )
            parameters.append(param)
        
        return parameters
    
    def _get_type_hint(self, annotation: Optional[ast.expr]) -> Optional[str]:
        """Extract type hint as string."""
        if annotation is None:
            return None
        
        try:
            return ast.unparse(annotation)
        except Exception:
            # Fallback for complex annotations
            return self._get_name_from_node(annotation)
    
    def _get_default_value(self, node: Optional[ast.expr]) -> Optional[str]:
        """Extract default value as string."""
        if node is None:
            return None
        
        try:
            return ast.unparse(node)
        except Exception:
            return repr(node)
    
    def _get_decorator_name(self, node: ast.expr) -> str:
        """Extract decorator name."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return ast.unparse(node)
        elif isinstance(node, ast.Call):
            # Decorator with arguments: @decorator(args)
            func = node.func
            if isinstance(func, ast.Name):
                return func.id
            elif isinstance(func, ast.Attribute):
                return ast.unparse(func)
        
        try:
            return ast.unparse(node)
        except Exception:
            return "unknown_decorator"
    
    def _get_name_from_node(self, node: ast.expr) -> Optional[str]:
        """Extract name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            try:
                return ast.unparse(node)
            except Exception:
                return None
        elif isinstance(node, ast.Subscript):
            # For generic types like List[str]
            try:
                return ast.unparse(node)
            except Exception:
                return None
        return None
    
    def extract_comments(self, source_code: str) -> list[Comment]:
        """
        Extract comments from source code.
        
        Parameters
        ----------
        source_code : str
            Python source code
            
        Returns
        -------
        list[Comment]
            List of comments with line numbers
        """
        comments = []
        lines = source_code.split('\n')
        
        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith('#'):
                comment_text = stripped[1:].strip()
                if comment_text:  # Ignore empty comments
                    comment = Comment(text=comment_text, line=i)
                    comments.append(comment)
        
        self.logger.debug(f"Extracted {len(comments)} comments")
        return comments
    
    def extract_global_variables(self, tree: ast.Module) -> list[tuple[str, Optional[str], Optional[str]]]:
        """
        Extract module-level global variables.
        
        Parameters
        ----------
        tree : ast.Module
            Parsed AST tree
            
        Returns
        -------
        list[tuple[str, Optional[str], Optional[str]]]
            List of (name, type_hint, default_value) tuples
        """
        variables = []
        
        for node in tree.body:
            if isinstance(node, ast.AnnAssign):
                # Type annotated: x: int = 5
                name = self._get_name_from_node(node.target)
                type_hint = self._get_type_hint(node.annotation)
                default = self._get_default_value(node.value) if node.value else None
                
                if name and name.isupper():  # Constants in UPPER_CASE
                    continue
                
                if name:
                    variables.append((name, type_hint, default))
            
            elif isinstance(node, ast.Assign):
                # Simple assignment: x = 5
                for target in node.targets:
                    name = self._get_name_from_node(target)
                    if name and not name.isupper():  # Skip constants
                        default = self._get_default_value(node.value)
                        variables.append((name, None, default))
        
        self.logger.debug(f"Extracted {len(variables)} global variables")
        return variables
    
    def detect_sql_in_strings(self, tree: ast.Module) -> list[tuple[str, int, bool]]:
        """
        Detect SQL queries in string literals and f-strings.
        
        Parameters
        ----------
        tree : ast.Module
            Parsed AST tree
            
        Returns
        -------
        list[tuple[str, int, bool]]
            List of (query, line, is_safe) tuples
            is_safe=False for f-strings (potential SQL injection)
        """
        sql_queries = []
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
        
        for node in ast.walk(tree):
            # Regular strings
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                value_upper = node.value.upper().strip()
                if any(keyword in value_upper for keyword in sql_keywords):
                    sql_queries.append((node.value, node.lineno, True))
            
            # F-strings (potential SQL injection)
            elif isinstance(node, ast.JoinedStr):
                # F-string detected
                try:
                    # Try to reconstruct the f-string
                    parts = []
                    for value in node.values:
                        if isinstance(value, ast.Constant):
                            parts.append(str(value.value))
                        else:
                            parts.append("{}")
                    
                    query = ''.join(parts)
                    query_upper = query.upper()
                    
                    if any(keyword in query_upper for keyword in sql_keywords):
                        sql_queries.append((query, node.lineno, False))  # Not safe!
                except Exception:
                    pass
        
        self.logger.debug(f"Detected {len(sql_queries)} SQL queries")
        return sql_queries
    
    def detect_hardcoded_secrets(self, source_code: str) -> list[tuple[str, str, int]]:
        """
        Detect potential hardcoded secrets in source code.
        
        Parameters
        ----------
        source_code : str
            Python source code
            
        Returns
        -------
        list[tuple[str, str, int]]
            List of (variable_name, value, line) tuples
        """
        import re
        
        secrets = []
        secret_patterns = [
            (r'API[_-]?KEY', 'API_KEY'),
            (r'SECRET[_-]?KEY', 'SECRET_KEY'),
            (r'PASSWORD', 'PASSWORD'),
            (r'TOKEN', 'TOKEN'),
            (r'AUTH', 'AUTH'),
            (r'CREDENTIAL', 'CREDENTIAL'),
        ]
        
        lines = source_code.split('\n')
        
        for i, line in enumerate(lines, start=1):
            # Skip comments
            if line.strip().startswith('#'):
                continue
            
            for pattern, secret_type in secret_patterns:
                # Look for assignments
                match = re.search(rf'({pattern})\s*=\s*["\'](.+?)["\']', line, re.IGNORECASE)
                if match:
                    var_name = match.group(1)
                    value = match.group(2)
                    
                    # Skip empty values, placeholders, environment variable references
                    if value and value not in ['', 'your-key-here', 'placeholder', '${', '{{']:
                        secrets.append((var_name, value, i))
        
        self.logger.debug(f"Detected {len(secrets)} potential hardcoded secrets")
        return secrets
