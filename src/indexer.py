#!/usr/bin/env python3
"""
Code Indexer for PY-Indexer v3.0.

Creates indexes from parsed Python files:
- Names index (all identifiers)
- Files index (file paths)
- Default values index
- Code analysis (mutable defaults, SQL injections, secrets, etc.)

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from parser import ParsedFile, FunctionDef, ClassDef, Parameter
from utils.utils_logger import get_logger
from utils.utils_hash import hash_object

logger = get_logger(__name__)


@dataclass
class MutableDefault:
    """Represents a mutable default argument issue."""
    function_name: str
    file_index: int
    line: int
    parameter_name: str
    default_value: str
    default_type: str  # list, dict, set


@dataclass
class SQLInjection:
    """Represents a potential SQL injection."""
    file_index: int
    line: int
    query: str
    is_safe: bool  # False for f-strings


@dataclass
class HardcodedSecret:
    """Represents a hardcoded secret."""
    variable_name: str
    file_index: int
    line: int
    secret_type: str  # API_KEY, PASSWORD, TOKEN, etc.


@dataclass
class GlobalVariable:
    """Represents a global variable (not a constant)."""
    name: str
    file_index: int
    line: int
    type_hint: Optional[str] = None
    has_type_hint: bool = False


@dataclass
class LoggingUsage:
    """Represents logging usage in a function."""
    function_name: str
    file_index: int
    line: int
    has_logging: bool


@dataclass
class MissingTypeHint:
    """Represents a function without type hints."""
    function_name: str
    file_index: int
    line: int
    is_public: bool


@dataclass
class MissingDocstring:
    """Represents a function/class without docstring."""
    name: str
    type: str  # function, class
    file_index: int
    line: int
    is_public: bool


@dataclass
class ClassDependency:
    """Represents class dependencies for DI analysis."""
    class_name: str
    file_index: int
    line: int
    dependencies: list[str]  # Classes created inside __init__
    uses_di: bool  # True if dependencies passed via __init__


class CodeIndexer:
    """
    Code indexer for PY-Indexer v3.0.
    
    Creates indexes from parsed files and performs code analysis.
    """
    
    def __init__(self, hash_length: int = 16):
        """
        Initialize indexer.
        
        Parameters
        ----------
        hash_length : int, optional
            Hash length for object hashing (default: 16)
        """
        self.logger = get_logger(__name__)
        self.hash_length = hash_length
        
        # Indexes
        self.names: list[str] = []
        self.files: list[str] = []
        self.default_values: list[str] = []
        
        # Name to index mapping
        self._name_to_idx: dict[str, int] = {}
        self._file_to_idx: dict[str, int] = {}
        self._default_to_idx: dict[str, int] = {}
        
        # Analysis results
        self.mutable_defaults: list[MutableDefault] = []
        self.sql_injections: list[SQLInjection] = []
        self.hardcoded_secrets: list[HardcodedSecret] = []
        self.global_variables: list[GlobalVariable] = []
        self.logging_usage: list[LoggingUsage] = []
        self.missing_type_hints: list[MissingTypeHint] = []
        self.missing_docstrings: list[MissingDocstring] = []
        self.class_dependencies: list[ClassDependency] = []
    
    def index_parsed_files(self, parsed_files: list[ParsedFile]) -> None:
        """
        Index list of parsed files.
        
        Parameters
        ----------
        parsed_files : list[ParsedFile]
            List of parsed Python files
        """
        self.logger.info(f"Indexing {len(parsed_files)} parsed files")
        
        for parsed_file in parsed_files:
            if parsed_file is None:
                continue
            
            # Index file
            file_idx = self._add_file(parsed_file.file_path)
            
            # Index names from imports
            for imp in parsed_file.imports:
                self._add_name(imp.module)
                for name in imp.names:
                    self._add_name(name)
            
            # Index classes
            for cls in parsed_file.classes:
                self._index_class(cls, file_idx)
            
            # Index functions
            for func in parsed_file.functions:
                self._index_function(func, file_idx)
            
            # Analyze code
            self._analyze_file(parsed_file, file_idx)
        
        self.logger.info(
            f"Indexing complete: "
            f"{len(self.names)} names, "
            f"{len(self.files)} files, "
            f"{len(self.default_values)} default values"
        )
    
    def _add_name(self, name: str) -> int:
        """
        Add name to index.
        
        Parameters
        ----------
        name : str
            Name to add
            
        Returns
        -------
        int
            Index of the name
        """
        if name in self._name_to_idx:
            return self._name_to_idx[name]
        
        idx = len(self.names)
        self.names.append(name)
        self._name_to_idx[name] = idx
        return idx
    
    def _add_file(self, file_path: str) -> int:
        """
        Add file to index.
        
        Parameters
        ----------
        file_path : str
            File path to add
            
        Returns
        -------
        int
            Index of the file
        """
        if file_path in self._file_to_idx:
            return self._file_to_idx[file_path]
        
        idx = len(self.files)
        self.files.append(file_path)
        self._file_to_idx[file_path] = idx
        return idx
    
    def _add_default_value(self, default: str) -> int:
        """
        Add default value to index.
        
        Parameters
        ----------
        default : str
            Default value to add
            
        Returns
        -------
        int
            Index of the default value
        """
        if default in self._default_to_idx:
            return self._default_to_idx[default]
        
        idx = len(self.default_values)
        self.default_values.append(default)
        self._default_to_idx[default] = idx
        return idx
    
    def _index_class(self, cls: ClassDef, file_idx: int) -> None:
        """Index class definition."""
        # Add class name
        self._add_name(cls.name)
        
        # Add base classes
        for base in cls.bases:
            self._add_name(base)
        
        # Add decorators
        for dec in cls.decorators:
            self._add_name(dec)
        
        # Add attributes
        for attr in cls.attributes:
            self._add_name(attr.name)
            if attr.type_hint:
                self._add_name(attr.type_hint)
            if attr.default:
                self._add_default_value(attr.default)
        
        # Index methods
        for method in cls.methods:
            self._index_function(method, file_idx)
        
        # Check for missing docstring
        if not cls.docstring and not cls.name.startswith('_'):
            missing = MissingDocstring(
                name=cls.name,
                type='class',
                file_index=file_idx,
                line=cls.line_start,
                is_public=not cls.name.startswith('_')
            )
            self.missing_docstrings.append(missing)
        
        # Analyze class dependencies
        self._analyze_class_dependencies(cls, file_idx)
    
    def _index_function(self, func: FunctionDef, file_idx: int) -> None:
        """Index function definition."""
        # Add function name
        self._add_name(func.name)
        
        # Add decorators
        for dec in func.decorators:
            self._add_name(dec)
        
        # Add parameters
        for param in func.parameters:
            self._add_name(param.name)
            
            if param.type_hint:
                self._add_name(param.type_hint)
            
            if param.default:
                self._add_default_value(param.default)
                
                # Check for mutable defaults
                if self._is_mutable_default(param.default):
                    mutable = MutableDefault(
                        function_name=func.name,
                        file_index=file_idx,
                        line=func.line_start,
                        parameter_name=param.name,
                        default_value=param.default,
                        default_type=self._get_mutable_type(param.default)
                    )
                    self.mutable_defaults.append(mutable)
        
        # Add return type
        if func.return_type:
            self._add_name(func.return_type)
        
        # Check for missing type hints
        is_public = not func.name.startswith('_')
        if is_public and not self._has_complete_type_hints(func):
            missing = MissingTypeHint(
                function_name=func.name,
                file_index=file_idx,
                line=func.line_start,
                is_public=is_public
            )
            self.missing_type_hints.append(missing)
        
        # Check for missing docstring
        if not func.docstring and is_public:
            missing = MissingDocstring(
                name=func.name,
                type='function',
                file_index=file_idx,
                line=func.line_start,
                is_public=is_public
            )
            self.missing_docstrings.append(missing)
    
    def _analyze_file(self, parsed_file: ParsedFile, file_idx: int) -> None:
        """Perform code analysis on parsed file."""
        from parser import ASTParser
        import ast
        
        try:
            # Parse file again for detailed analysis
            from utils.utils_file import read_python_file
            content = read_python_file(parsed_file.file_path)
            tree = ast.parse(content, filename=parsed_file.file_path)
            
            parser = ASTParser()
            
            # Detect SQL injections
            sql_queries = parser.detect_sql_in_strings(tree)
            for query, line, is_safe in sql_queries:
                injection = SQLInjection(
                    file_index=file_idx,
                    line=line,
                    query=query[:100],  # Truncate long queries
                    is_safe=is_safe
                )
                self.sql_injections.append(injection)
            
            # Detect hardcoded secrets
            secrets = parser.detect_hardcoded_secrets(content)
            for var_name, value, line in secrets:
                secret = HardcodedSecret(
                    variable_name=var_name,
                    file_index=file_idx,
                    line=line,
                    secret_type=self._detect_secret_type(var_name)
                )
                self.hardcoded_secrets.append(secret)
            
            # Detect global variables
            global_vars = parser.extract_global_variables(tree)
            for name, type_hint, default in global_vars:
                global_var = GlobalVariable(
                    name=name,
                    file_index=file_idx,
                    line=0,  # TODO: extract line number
                    type_hint=type_hint,
                    has_type_hint=type_hint is not None
                )
                self.global_variables.append(global_var)
            
            # Check logging usage
            self._analyze_logging_usage(parsed_file, file_idx, content)
            
        except Exception as e:
            self.logger.error(f"Error analyzing file {parsed_file.file_path}: {e}", exc_info=True)
    
    def _is_mutable_default(self, default: str) -> bool:
        """
        Check if default value is mutable.
        
        Parameters
        ----------
        default : str
            Default value as string
            
        Returns
        -------
        bool
            True if mutable, False otherwise
        """
        default_stripped = default.strip()
        
        # Check for list
        if default_stripped.startswith('[') and default_stripped.endswith(']'):
            return True
        
        # Check for dict
        if default_stripped.startswith('{') and default_stripped.endswith('}'):
            return True
        
        # Check for set
        if default_stripped.startswith('set(') or default_stripped.startswith('{') and ':' not in default_stripped:
            return True
        
        # Check for list(), dict(), set() calls
        if default_stripped in ['list()', 'dict()', 'set()']:
            return True
        
        return False
    
    def _get_mutable_type(self, default: str) -> str:
        """Get type of mutable default."""
        default_stripped = default.strip()
        
        if default_stripped.startswith('[') or default_stripped == 'list()':
            return 'list'
        elif default_stripped.startswith('{') and ':' in default_stripped or default_stripped == 'dict()':
            return 'dict'
        elif default_stripped.startswith('{') or default_stripped == 'set()' or default_stripped.startswith('set('):
            return 'set'
        
        return 'unknown'
    
    def _has_complete_type_hints(self, func: FunctionDef) -> bool:
        """
        Check if function has complete type hints.
        
        Parameters
        ----------
        func : FunctionDef
            Function definition
            
        Returns
        -------
        bool
            True if has type hints for all parameters and return type
        """
        # Skip special methods
        if func.name.startswith('__') and func.name.endswith('__'):
            return True
        
        # Check parameters (skip self, cls)
        for param in func.parameters:
            if param.name in ['self', 'cls']:
                continue
            if param.kind in ['*args', '**kwargs']:
                continue
            if not param.type_hint:
                return False
        
        # Check return type (skip __init__)
        if func.name != '__init__' and not func.return_type:
            return False
        
        return True
    
    def _detect_secret_type(self, var_name: str) -> str:
        """Detect type of secret from variable name."""
        var_upper = var_name.upper()
        
        if 'API' in var_upper and 'KEY' in var_upper:
            return 'API_KEY'
        elif 'SECRET' in var_upper:
            return 'SECRET_KEY'
        elif 'PASSWORD' in var_upper:
            return 'PASSWORD'
        elif 'TOKEN' in var_upper:
            return 'TOKEN'
        elif 'AUTH' in var_upper:
            return 'AUTH'
        elif 'CREDENTIAL' in var_upper:
            return 'CREDENTIAL'
        
        return 'UNKNOWN'
    
    def _analyze_logging_usage(self, parsed_file: ParsedFile, file_idx: int, content: str) -> None:
        """Analyze logging usage in functions."""
        for func in parsed_file.functions:
            has_logging = self._has_logging_in_function(func, content)
            
            usage = LoggingUsage(
                function_name=func.name,
                file_index=file_idx,
                line=func.line_start,
                has_logging=has_logging
            )
            self.logging_usage.append(usage)
        
        # Check methods in classes
        for cls in parsed_file.classes:
            for method in cls.methods:
                has_logging = self._has_logging_in_function(method, content)
                
                usage = LoggingUsage(
                    function_name=f"{cls.name}.{method.name}",
                    file_index=file_idx,
                    line=method.line_start,
                    has_logging=has_logging
                )
                self.logging_usage.append(usage)
    
    def _has_logging_in_function(self, func: FunctionDef, content: str) -> bool:
        """
        Check if function uses logging.
        
        Parameters
        ----------
        func : FunctionDef
            Function definition
        content : str
            Source code content
            
        Returns
        -------
        bool
            True if function contains logger calls
        """
        lines = content.split('\n')
        
        # Get function body lines
        if func.line_end > len(lines):
            return False
        
        func_lines = lines[func.line_start - 1:func.line_end]
        func_body = '\n'.join(func_lines)
        
        # Check for logging calls
        logging_patterns = [
            'logger.debug',
            'logger.info',
            'logger.warning',
            'logger.error',
            'logger.critical',
            'logger.exception',
            'logging.debug',
            'logging.info',
            'logging.warning',
            'logging.error',
            'logging.critical'
        ]
        
        for pattern in logging_patterns:
            if pattern in func_body:
                return True
        
        return False
    
    def _analyze_class_dependencies(self, cls: ClassDef, file_idx: int) -> None:
        """
        Analyze class dependencies for Dependency Injection check.
        
        Parameters
        ----------
        cls : ClassDef
            Class definition
        file_idx : int
            File index
        """
        # Find __init__ method
        init_method = None
        for method in cls.methods:
            if method.name == '__init__':
                init_method = method
                break
        
        if not init_method:
            return
        
        # Check if dependencies are passed via __init__ parameters
        init_params = [p.name for p in init_method.parameters if p.name not in ['self', 'cls']]
        uses_di = len(init_params) > 0
        
        # TODO: Detect classes instantiated inside __init__ (sign of bad DI)
        # This would require analyzing AST of __init__ body
        dependencies = []
        
        dep = ClassDependency(
            class_name=cls.name,
            file_index=file_idx,
            line=cls.line_start,
            dependencies=dependencies,
            uses_di=uses_di
        )
        self.class_dependencies.append(dep)
    
    def get_name_index(self, name: str) -> Optional[int]:
        """
        Get index of name.
        
        Parameters
        ----------
        name : str
            Name to look up
            
        Returns
        -------
        int | None
            Index of name, or None if not found
        """
        return self._name_to_idx.get(name)
    
    def get_file_index(self, file_path: str) -> Optional[int]:
        """
        Get index of file.
        
        Parameters
        ----------
        file_path : str
            File path to look up
            
        Returns
        -------
        int | None
            Index of file, or None if not found
        """
        return self._file_to_idx.get(file_path)
    
    def get_default_index(self, default: str) -> Optional[int]:
        """
        Get index of default value.
        
        Parameters
        ----------
        default : str
            Default value to look up
            
        Returns
        -------
        int | None
            Index of default, or None if not found
        """
        return self._default_to_idx.get(default)
    
    def get_statistics(self) -> dict:
        """
        Get indexing statistics.
        
        Returns
        -------
        dict
            Statistics about indexed data
        """
        return {
            'total_names': len(self.names),
            'total_files': len(self.files),
            'total_defaults': len(self.default_values),
            'mutable_defaults_count': len(self.mutable_defaults),
            'sql_injections_count': len(self.sql_injections),
            'hardcoded_secrets_count': len(self.hardcoded_secrets),
            'global_variables_count': len(self.global_variables),
            'missing_type_hints_count': len(self.missing_type_hints),
            'missing_docstrings_count': len(self.missing_docstrings),
            'classes_with_di': sum(1 for dep in self.class_dependencies if dep.uses_di),
            'classes_without_di': sum(1 for dep in self.class_dependencies if not dep.uses_di)
        }
