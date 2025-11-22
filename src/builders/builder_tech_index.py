#!/usr/bin/env python3
"""
TECH-INDEX Builder for PY-Indexer v3.0.

Builds compact TECH-INDEX format from indexed data:
- Uses numeric references for all strings
- Compresses data with справочники (names, files, defaults)
- Applies v3.0 schema extensions
- Optional GZIP compression for names array

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

import gzip
import base64
from datetime import datetime
from typing import Optional

from parser import ParsedFile, FunctionDef, ClassDef, Parameter
from indexer import CodeIndexer
from utils.utils_logger import get_logger
from utils.utils_hash import hash_object, hash_file
from utils.utils_file import get_file_size, get_file_modified

logger = get_logger(__name__)


class TechIndexBuilder:
    """
    Builder for TECH-INDEX v3.0 (compact format).
    
    Creates maximally compressed index using numeric references.
    """
    
    def __init__(
        self,
        indexer: CodeIndexer,
        project_name: str = "unknown",
        compress_names: bool = False,
        hash_length: int = 16
    ):
        """
        Initialize TECH-INDEX builder.
        
        Parameters
        ----------
        indexer : CodeIndexer
            Populated code indexer
        project_name : str, optional
            Project name for metadata (default: "unknown")
        compress_names : bool, optional
            Compress names array with GZIP+Base64 (default: False)
        hash_length : int, optional
            Hash length for objects (default: 16)
        """
        self.logger = get_logger(__name__)
        self.indexer = indexer
        self.project_name = project_name
        self.compress_names = compress_names
        self.hash_length = hash_length
    
    def build(self, parsed_files: list[ParsedFile]) -> dict:
        """
        Build TECH-INDEX from parsed files.
        
        Parameters
        ----------
        parsed_files : list[ParsedFile]
            List of parsed Python files
            
        Returns
        -------
        dict
            TECH-INDEX v3.0 structure
        """
        self.logger.info(f"Building TECH-INDEX for {len(parsed_files)} files")
        
        index = {
            "meta": self._build_meta(),
            "names": self._build_names(),
            "files": self.indexer.files,
            "filesizes": self._build_filesizes(),
            "modules": self._build_modules(parsed_files),
            "classes": self._build_classes(parsed_files),
            "functions": self._build_functions(parsed_files),
            "parameters": self._build_parameters(parsed_files),
            "decorators": self._build_decorators(parsed_files),
            "docstrings": self._build_docstrings(parsed_files),
            "imports": self._build_imports(parsed_files),
            "comments": self._build_comments(parsed_files),
            "typehints": self._build_typehints(parsed_files),
            "defaults": self.indexer.default_values,
            "defaultissues": self._build_default_issues(),
            "sqlqueries": self._build_sql_queries(),
            "hardcodedsecrets": self._build_hardcoded_secrets(),
            "loggingusage": self._build_logging_usage(),
            "globalvars": self._build_global_vars(),
            "classdeps": self._build_class_deps(),
            "docstringformats": self._build_docstring_formats(parsed_files),
            "testcoverage": self._build_test_coverage(parsed_files)
        }
        
        self.logger.info("TECH-INDEX built successfully")
        return index
    
    def _build_meta(self) -> dict:
        """Build metadata section."""
        return {
            "version": "3.0",
            "schema_version": "3.0",
            "generated": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "project": self.project_name,
            "backward_compatible_with": ["2.1", "2.0"]
        }
    
    def _build_names(self) -> list[str] | str:
        """
        Build names array.
        
        Returns
        -------
        list[str] | str
            Names array, or GZIP+Base64 compressed string if compress_names=True
        """
        if not self.compress_names:
            return self.indexer.names
        
        # Compress names with GZIP
        import json
        names_json = json.dumps(self.indexer.names, ensure_ascii=False)
        compressed = gzip.compress(names_json.encode('utf-8'))
        encoded = base64.b64encode(compressed).decode('ascii')
        
        self.logger.info(
            f"Compressed names: {len(names_json)} -> {len(encoded)} bytes "
            f"({len(encoded) / len(names_json) * 100:.1f}%)"
        )
        
        return encoded
    
    def _build_filesizes(self) -> list[int]:
        """Build file sizes array."""
        sizes = []
        for file_path in self.indexer.files:
            try:
                size = get_file_size(file_path)
                sizes.append(size)
            except Exception as e:
                self.logger.warning(f"Cannot get size for {file_path}: {e}")
                sizes.append(0)
        return sizes
    
    def _build_modules(self, parsed_files: list[ParsedFile]) -> list[list]:
        """
        Build modules array.
        
        Format: [name_idx, line_start, parent_idx]
        """
        modules = []
        
        for parsed_file in parsed_files:
            if parsed_file is None:
                continue
            
            name_idx = self.indexer.get_name_index(parsed_file.module_name)
            if name_idx is None:
                name_idx = self.indexer._add_name(parsed_file.module_name)
            
            file_idx = self.indexer.get_file_index(parsed_file.file_path)
            
            module = [name_idx, 0, -1]  # name, line_start, parent (no parent for modules)
            modules.append(module)
        
        return modules
    
    def _build_classes(self, parsed_files: list[ParsedFile]) -> list[list]:
        """
        Build classes array.
        
        Format: [name_idx, line_start, file_idx, bases[], decorators[], parent_idx, attributes[]]
        """
        classes = []
        
        for parsed_file in parsed_files:
            if parsed_file is None:
                continue
            
            file_idx = self.indexer.get_file_index(parsed_file.file_path)
            
            for cls in parsed_file.classes:
                name_idx = self.indexer.get_name_index(cls.name)
                
                # Base classes
                bases = [self.indexer.get_name_index(base) for base in cls.bases]
                bases = [b for b in bases if b is not None]
                
                # Decorators
                decorators = [self.indexer.get_name_index(dec) for dec in cls.decorators]
                decorators = [d for d in decorators if d is not None]
                
                # Attributes
                attributes = []
                for attr in cls.attributes:
                    attr_name_idx = self.indexer.get_name_index(attr.name)
                    if attr_name_idx is not None:
                        attributes.append(attr_name_idx)
                
                class_entry = [
                    name_idx,
                    cls.line_start,
                    file_idx,
                    bases,
                    decorators,
                    -1,  # parent_idx (always -1 for top-level classes)
                    attributes
                ]
                classes.append(class_entry)
        
        return classes
    
    def _build_functions(self, parsed_files: list[ParsedFile]) -> list[list]:
        """
        Build functions array.
        
        Format: [name_idx, line_start, file_idx]
        """
        functions = []
        
        for parsed_file in parsed_files:
            if parsed_file is None:
                continue
            
            file_idx = self.indexer.get_file_index(parsed_file.file_path)
            
            # Module-level functions
            for func in parsed_file.functions:
                name_idx = self.indexer.get_name_index(func.name)
                func_entry = [name_idx, func.line_start, file_idx]
                functions.append(func_entry)
            
            # Class methods
            for cls in parsed_file.classes:
                for method in cls.methods:
                    name_idx = self.indexer.get_name_index(method.name)
                    func_entry = [name_idx, method.line_start, file_idx]
                    functions.append(func_entry)
        
        return functions
    
    def _build_parameters(self, parsed_files: list[ParsedFile]) -> dict[str, list[int]]:
        """
        Build parameters mapping.
        
        Format: {"function_index": [param_name_idx, param_name_idx, ...]}
        """
        parameters = {}
        func_index = 0
        
        for parsed_file in parsed_files:
            if parsed_file is None:
                continue
            
            # Module-level functions
            for func in parsed_file.functions:
                param_indices = []
                for param in func.parameters:
                    if param.name not in ['self', 'cls']:
                        param_idx = self.indexer.get_name_index(param.name)
                        if param_idx is not None:
                            param_indices.append(param_idx)
                
                parameters[str(func_index)] = param_indices
                func_index += 1
            
            # Class methods
            for cls in parsed_file.classes:
                for method in cls.methods:
                    param_indices = []
                    for param in method.parameters:
                        if param.name not in ['self', 'cls']:
                            param_idx = self.indexer.get_name_index(param.name)
                            if param_idx is not None:
                                param_indices.append(param_idx)
                    
                    parameters[str(func_index)] = param_indices
                    func_index += 1
        
        return parameters
    
    def _build_decorators(self, parsed_files: list[ParsedFile]) -> list[list]:
        """
        Build decorators array.
        
        Format: [decorator_name_idx, target_type, target_idx]
        target_type: 0=function, 1=class
        """
        decorators = []
        
        func_index = 0
        class_index = 0
        
        for parsed_file in parsed_files:
            if parsed_file is None:
                continue
            
            # Function decorators
            for func in parsed_file.functions:
                for dec in func.decorators:
                    dec_idx = self.indexer.get_name_index(dec)
                    if dec_idx is not None:
                        decorators.append([dec_idx, 0, func_index])
                func_index += 1
            
            # Class decorators
            for cls in parsed_file.classes:
                for dec in cls.decorators:
                    dec_idx = self.indexer.get_name_index(dec)
                    if dec_idx is not None:
                        decorators.append([dec_idx, 1, class_index])
                
                # Method decorators
                for method in cls.methods:
                    for dec in method.decorators:
                        dec_idx = self.indexer.get_name_index(dec)
                        if dec_idx is not None:
                            decorators.append([dec_idx, 0, func_index])
                    func_index += 1
                
                class_index += 1
        
        return decorators
    
    def _build_docstrings(self, parsed_files: list[ParsedFile]) -> list[list]:
        """
        Build docstrings array.
        
        Format: [target_idx, target_type, docstring_text]
        target_type: 0=module, 1=class, 2=function
        """
        docstrings = []
        
        module_idx = 0
        class_idx = 0
        func_idx = 0
        
        for parsed_file in parsed_files:
            if parsed_file is None:
                continue
            
            # Module docstring
            if parsed_file.module_docstring:
                docstrings.append([module_idx, 0, parsed_file.module_docstring])
            module_idx += 1
            
            # Function docstrings
            for func in parsed_file.functions:
                if func.docstring:
                    docstrings.append([func_idx, 2, func.docstring])
                func_idx += 1
            
            # Class docstrings
            for cls in parsed_file.classes:
                if cls.docstring:
                    docstrings.append([class_idx, 1, cls.docstring])
                
                # Method docstrings
                for method in cls.methods:
                    if method.docstring:
                        docstrings.append([func_idx, 2, method.docstring])
                    func_idx += 1
                
                class_idx += 1
        
        return docstrings
    
    def _build_imports(self, parsed_files: list[ParsedFile]) -> list[list]:
        """
        Build imports array.
        
        Format: [module_name_idx, file_idx, line, level]
        """
        imports = []
        
        for parsed_file in parsed_files:
            if parsed_file is None:
                continue
            
            file_idx = self.indexer.get_file_index(parsed_file.file_path)
            
            for imp in parsed_file.imports:
                module_idx = self.indexer.get_name_index(imp.module)
                if module_idx is not None:
                    imports.append([module_idx, file_idx, imp.line, imp.level])
        
        return imports
    
    def _build_comments(self, parsed_files: list[ParsedFile]) -> list[list]:
        """
        Build comments array.
        
        Format: [file_idx, line, text]
        """
        comments = []
        
        for parsed_file in parsed_files:
            if parsed_file is None:
                continue
            
            file_idx = self.indexer.get_file_index(parsed_file.file_path)
            
            for comment in parsed_file.comments:
                comments.append([file_idx, comment.line, comment.text])
        
        return comments
    
    def _build_typehints(self, parsed_files: list[ParsedFile]) -> list[list]:
        """
        Build type hints array.
        
        Format: [func_idx, [param_name_idx, type_idx], return_type_idx]
        """
        typehints = []
        func_idx = 0
        
        for parsed_file in parsed_files:
            if parsed_file is None:
                continue
            
            for func in parsed_file.functions:
                params_with_types = []
                for param in func.parameters:
                    if param.type_hint:
                        param_name_idx = self.indexer.get_name_index(param.name)
                        type_idx = self.indexer.get_name_index(param.type_hint)
                        if param_name_idx is not None and type_idx is not None:
                            params_with_types.extend([param_name_idx, type_idx])
                
                return_type_idx = None
                if func.return_type:
                    return_type_idx = self.indexer.get_name_index(func.return_type)
                
                if params_with_types or return_type_idx:
                    typehints.append([func_idx, params_with_types, return_type_idx])
                
                func_idx += 1
            
            for cls in parsed_file.classes:
                for method in cls.methods:
                    params_with_types = []
                    for param in method.parameters:
                        if param.type_hint:
                            param_name_idx = self.indexer.get_name_index(param.name)
                            type_idx = self.indexer.get_name_index(param.type_hint)
                            if param_name_idx is not None and type_idx is not None:
                                params_with_types.extend([param_name_idx, type_idx])
                    
                    return_type_idx = None
                    if method.return_type:
                        return_type_idx = self.indexer.get_name_index(method.return_type)
                    
                    if params_with_types or return_type_idx:
                        typehints.append([func_idx, params_with_types, return_type_idx])
                    
                    func_idx += 1
        
        return typehints
    
    def _build_default_issues(self) -> list[list]:
        """
        Build mutable defaults issues array.
        
        Format: [func_name_idx, file_idx, line, param_name_idx, default_idx]
        """
        issues = []
        
        for mutable in self.indexer.mutable_defaults:
            func_name_idx = self.indexer.get_name_index(mutable.function_name)
            param_name_idx = self.indexer.get_name_index(mutable.parameter_name)
            default_idx = self.indexer.get_default_index(mutable.default_value)
            
            if func_name_idx is not None and param_name_idx is not None and default_idx is not None:
                issues.append([
                    func_name_idx,
                    mutable.file_index,
                    mutable.line,
                    param_name_idx,
                    default_idx
                ])
        
        return issues
    
    def _build_sql_queries(self) -> list[list]:
        """
        Build SQL queries array.
        
        Format: [file_idx, line, is_safe]
        """
        queries = []
        
        for sql in self.indexer.sql_injections:
            queries.append([sql.file_index, sql.line, sql.is_safe])
        
        return queries
    
    def _build_hardcoded_secrets(self) -> list[list]:
        """
        Build hardcoded secrets array.
        
        Format: [var_name_idx, file_idx, line]
        """
        secrets = []
        
        for secret in self.indexer.hardcoded_secrets:
            var_name_idx = self.indexer.get_name_index(secret.variable_name)
            if var_name_idx is not None:
                secrets.append([var_name_idx, secret.file_index, secret.line])
        
        return secrets
    
    def _build_logging_usage(self) -> list[list]:
        """
        Build logging usage array.
        
        Format: [func_name_idx, file_idx, has_logging]
        """
        usage = []
        
        for log in self.indexer.logging_usage:
            func_name_idx = self.indexer.get_name_index(log.function_name)
            if func_name_idx is not None:
                usage.append([func_name_idx, log.file_index, log.has_logging])
        
        return usage
    
    def _build_global_vars(self) -> list[list]:
        """
        Build global variables array.
        
        Format: [var_name_idx, file_idx, has_type_hint]
        """
        global_vars = []
        
        for gvar in self.indexer.global_variables:
            var_name_idx = self.indexer.get_name_index(gvar.name)
            if var_name_idx is not None:
                global_vars.append([var_name_idx, gvar.file_index, gvar.has_type_hint])
        
        return global_vars
    
    def _build_class_deps(self) -> list[list]:
        """
        Build class dependencies array.
        
        Format: [class_name_idx, file_idx, uses_di]
        """
        deps = []
        
        for dep in self.indexer.class_dependencies:
            class_name_idx = self.indexer.get_name_index(dep.class_name)
            if class_name_idx is not None:
                deps.append([class_name_idx, dep.file_index, dep.uses_di])
        
        return deps
    
    def _build_docstring_formats(self, parsed_files: list[ParsedFile]) -> list[list]:
        """
        Build docstring formats array.
        
        Format: [func_idx, format_type]
        format_type: 0=numpy, 1=google, 2=sphinx, 3=none
        """
        formats = []
        func_idx = 0
        
        for parsed_file in parsed_files:
            if parsed_file is None:
                continue
            
            for func in parsed_file.functions:
                doc_format = self._detect_docstring_format(func.docstring)
                formats.append([func_idx, doc_format])
                func_idx += 1
            
            for cls in parsed_file.classes:
                for method in cls.methods:
                    doc_format = self._detect_docstring_format(method.docstring)
                    formats.append([func_idx, doc_format])
                    func_idx += 1
        
        return formats
    
    def _detect_docstring_format(self, docstring: Optional[str]) -> int:
        """
        Detect docstring format.
        
        Returns
        -------
        int
            0=numpy, 1=google, 2=sphinx, 3=none
        """
        if not docstring:
            return 3  # none
        
        # NumPy style: "Parameters\n----------"
        if "Parameters\n" in docstring and "----------" in docstring:
            return 0
        
        # Google style: "Args:"
        if "Args:" in docstring or "Returns:" in docstring:
            return 1
        
        # Sphinx style: ":param"
        if ":param" in docstring or ":type" in docstring or ":return" in docstring:
            return 2
        
        return 3  # none/unknown
    
    def _build_test_coverage(self, parsed_files: list[ParsedFile]) -> list[list]:
        """
        Build test coverage array.
        
        Format: [func_name_idx, has_test]
        """
        coverage = []
        
        # Simple heuristic: check if test_<function_name> exists
        all_function_names = set()
        test_function_names = set()
        
        for parsed_file in parsed_files:
            if parsed_file is None:
                continue
            
            for func in parsed_file.functions:
                all_function_names.add(func.name)
                if func.name.startswith('test_'):
                    # Extract tested function name
                    tested_name = func.name[5:]  # Remove 'test_' prefix
                    test_function_names.add(tested_name)
            
            for cls in parsed_file.classes:
                for method in cls.methods:
                    full_name = f"{cls.name}.{method.name}"
                    all_function_names.add(full_name)
                    if method.name.startswith('test_'):
                        tested_name = method.name[5:]
                        test_function_names.add(tested_name)
        
        # Build coverage array
        for func_name in all_function_names:
            func_name_idx = self.indexer.get_name_index(func_name)
            if func_name_idx is not None:
                has_test = func_name in test_function_names
                coverage.append([func_name_idx, has_test])
        
        return coverage
