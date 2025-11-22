#!/usr/bin/env python3
"""
TECH-LOCATION Builder for PY-Indexer v3.0.

Builds human-readable TECH-LOCATION format from TECH-INDEX:
- Expands numeric references to full names
- Uses readable format with full identifiers
- Easier for humans to read and understand

Author: PY-Indexer Development Team
Date: 2025-11-22
"""

from datetime import datetime
from typing import Optional

from utils.utils_logger import get_logger
from utils.utils_file import get_file_modified, get_file_hash

logger = get_logger(__name__)


class LocationBuilder:
    """
    Builder for TECH-LOCATION v3.0 (human-readable format).
    
    Converts compact TECH-INDEX to expanded location format.
    """
    
    def __init__(self, tech_index: dict, project_name: str = "unknown"):
        """
        Initialize TECH-LOCATION builder.
        
        Parameters
        ----------
        tech_index : dict
            Complete TECH-INDEX v3.0 structure
        project_name : str, optional
            Project name for metadata (default: "unknown")
        """
        self.logger = get_logger(__name__)
        self.tech_index = tech_index
        self.project_name = project_name
        
        # Extract справочники
        self.names = tech_index.get("names", [])
        self.files = tech_index.get("files", [])
        self.defaults = tech_index.get("defaults", [])
    
    def build(self) -> dict:
        """
        Build TECH-LOCATION from TECH-INDEX.
        
        Returns
        -------
        dict
            TECH-LOCATION v3.0 structure
        """
        self.logger.info("Building TECH-LOCATION from TECH-INDEX")
        
        location = {
            "meta": self._build_meta(),
            "paths": self.files,
            "modifieds": self._build_modifieds(),
            "hashes": self._build_hashes(),
            "files": self._expand_files(),
            "modules": self._expand_modules(),
            "classes": self._expand_classes(),
            "functions": self._expand_functions(),
            "decorators": self._expand_decorators(),
            "commenttexts": self._expand_comments(),
            "imports": self._expand_imports(),
            "comments": [],  # Empty in v3.0 (merged with commenttexts)
            "typehints": self._expand_typehints(),
            "mutabledefaults": self._expand_mutable_defaults(),
            "sqlqueries": self._expand_sql_queries(),
            "hardcodedsecrets": self._expand_hardcoded_secrets(),
            "loggingusage": self._expand_logging_usage(),
            "globalvars": self._expand_global_vars(),
            "classdeps": self._expand_class_deps(),
            "docstringformats": self._expand_docstring_formats(),
            "testcoverage": self._expand_test_coverage()
        }
        
        self.logger.info("TECH-LOCATION built successfully")
        return location
    
    def _build_meta(self) -> dict:
        """Build metadata section."""
        return {
            "version": "3.0",
            "generated": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            "project": self.project_name,
            "source": "tech-index-v3"
        }
    
    def _build_modifieds(self) -> list[str]:
        """Build modification times for all files."""
        modifieds = []
        for file_path in self.files:
            try:
                modified = get_file_modified(file_path, iso_format=True)
                modifieds.append(modified)
            except Exception as e:
                self.logger.warning(f"Cannot get modification time for {file_path}: {e}")
                modifieds.append("")
        return modifieds
    
    def _build_hashes(self) -> list[str]:
        """Build file hashes."""
        hashes = []
        for file_path in self.files:
            try:
                file_hash = get_file_hash(file_path, length=16)
                hashes.append(file_hash)
            except Exception as e:
                self.logger.warning(f"Cannot get hash for {file_path}: {e}")
                hashes.append("")
        return hashes
    
    def _expand_files(self) -> list[list]:
        """
        Expand files array.
        
        Format: [file_idx, line_end, size, classes_count, functions_count]
        """
        files_data = []
        
        # Get counts from tech_index
        classes = self.tech_index.get("classes", [])
        functions = self.tech_index.get("functions", [])
        
        for file_idx, file_path in enumerate(self.files):
            # Count classes in this file
            classes_count = sum(1 for cls in classes if cls[2] == file_idx)
            
            # Count functions in this file
            functions_count = sum(1 for func in functions if func[2] == file_idx)
            
            # Get file size
            try:
                from utils.utils_file import get_file_size
                size = get_file_size(file_path)
            except Exception:
                size = 0
            
            files_data.append([file_idx, 0, size, classes_count, functions_count])
        
        return files_data
    
    def _expand_modules(self) -> list[list]:
        """
        Expand modules array.
        
        Format: [name, file_idx, parent_idx, line_start, line_end, docstring]
        """
        modules = []
        modules_data = self.tech_index.get("modules", [])
        docstrings = self.tech_index.get("docstrings", [])
        
        for idx, module_data in enumerate(modules_data):
            name_idx, line_start, parent_idx = module_data
            name = self._get_name(name_idx)
            
            # Find docstring
            docstring = None
            for doc_data in docstrings:
                if doc_data[0] == idx and doc_data[1] == 0:  # module docstring
                    docstring = doc_data[2]
                    break
            
            modules.append([name, idx, parent_idx, line_start, 0, docstring])
        
        return modules
    
    def _expand_classes(self) -> list[list]:
        """
        Expand classes array.
        
        Format: [name, parent_idx, file_idx, line_start, line_end, def_line, end_line]
        """
        classes = []
        classes_data = self.tech_index.get("classes", [])
        
        for cls_data in classes_data:
            name_idx, line_start, file_idx, bases, decorators, parent_idx, attributes = cls_data
            name = self._get_name(name_idx)
            
            classes.append([
                name,
                parent_idx,
                file_idx,
                line_start,
                line_start,  # line_end (same for now)
                line_start,  # def_line
                line_start   # end_line
            ])
        
        return classes
    
    def _expand_functions(self) -> list[list]:
        """
        Expand functions array.
        
        Format: [name, parent_idx, file_idx, line_start, line_end, def_line, end_line]
        """
        functions = []
        functions_data = self.tech_index.get("functions", [])
        
        for func_data in functions_data:
            name_idx, line_start, file_idx = func_data
            name = self._get_name(name_idx)
            
            functions.append([
                name,
                -1,  # parent_idx (TBD)
                file_idx,
                line_start,
                line_start,  # line_end
                line_start,  # def_line
                line_start   # end_line
            ])
        
        return functions
    
    def _expand_decorators(self) -> list:
        """
        Expand decorators array.
        
        Format: [] (empty in TECH-LOCATION v3.0)
        """
        return []
    
    def _expand_comments(self) -> list[list]:
        """
        Expand comments array.
        
        Format: [text, file_idx, line]
        """
        comments = []
        comments_data = self.tech_index.get("comments", [])
        
        for comment_data in comments_data:
            file_idx, line, text = comment_data
            comments.append([text, file_idx, line])
        
        return comments
    
    def _expand_imports(self) -> list[list]:
        """
        Expand imports array.
        
        Format: [module_name, file_idx, line, level]
        """
        imports = []
        imports_data = self.tech_index.get("imports", [])
        
        for import_data in imports_data:
            module_idx, file_idx, line, level = import_data
            module_name = self._get_name(module_idx)
            imports.append([module_name, file_idx, line, level])
        
        return imports
    
    def _expand_typehints(self) -> list[list]:
        """
        Expand type hints array.
        
        Format: [func_name, [param_name, type, ...], return_type]
        """
        typehints = []
        typehints_data = self.tech_index.get("typehints", [])
        functions_data = self.tech_index.get("functions", [])
        
        for typehint_data in typehints_data:
            func_idx, params, return_type_idx = typehint_data
            
            # Get function name
            if func_idx < len(functions_data):
                func_name_idx = functions_data[func_idx][0]
                func_name = self._get_name(func_name_idx)
            else:
                func_name = "unknown"
            
            # Expand parameters
            expanded_params = []
            for i in range(0, len(params), 2):
                param_name = self._get_name(params[i])
                param_type = self._get_name(params[i + 1])
                expanded_params.extend([param_name, param_type])
            
            # Expand return type
            return_type = self._get_name(return_type_idx) if return_type_idx else None
            
            typehints.append([func_name, expanded_params, return_type])
        
        return typehints
    
    def _expand_mutable_defaults(self) -> list[list]:
        """
        Expand mutable defaults array.
        
        Format: [func_name, file_path, line, param_name, default_value, default_type]
        """
        mutable_defaults = []
        defaults_data = self.tech_index.get("defaultissues", [])
        
        for default_data in defaults_data:
            func_name_idx, file_idx, line, param_name_idx, default_idx = default_data
            
            func_name = self._get_name(func_name_idx)
            file_path = self._get_file(file_idx)
            param_name = self._get_name(param_name_idx)
            default_value = self._get_default(default_idx)
            
            # Detect type
            default_type = "list"
            if default_value.startswith('{'):
                default_type = "dict" if ':' in default_value else "set"
            
            mutable_defaults.append([
                func_name,
                file_path,
                line,
                param_name,
                default_value,
                default_type
            ])
        
        return mutable_defaults
    
    def _expand_sql_queries(self) -> list[list]:
        """
        Expand SQL queries array.
        
        Format: [file_path, line, is_safe]
        """
        sql_queries = []
        queries_data = self.tech_index.get("sqlqueries", [])
        
        for query_data in queries_data:
            file_idx, line, is_safe = query_data
            file_path = self._get_file(file_idx)
            sql_queries.append([file_path, line, is_safe])
        
        return sql_queries
    
    def _expand_hardcoded_secrets(self) -> list[list]:
        """
        Expand hardcoded secrets array.
        
        Format: [var_name, file_path, line]
        """
        secrets = []
        secrets_data = self.tech_index.get("hardcodedsecrets", [])
        
        for secret_data in secrets_data:
            var_name_idx, file_idx, line = secret_data
            var_name = self._get_name(var_name_idx)
            file_path = self._get_file(file_idx)
            secrets.append([var_name, file_path, line])
        
        return secrets
    
    def _expand_logging_usage(self) -> list[list]:
        """
        Expand logging usage array.
        
        Format: [func_name, file_path, has_logging]
        """
        logging_usage = []
        usage_data = self.tech_index.get("loggingusage", [])
        
        for usage in usage_data:
            func_name_idx, file_idx, has_logging = usage
            func_name = self._get_name(func_name_idx)
            file_path = self._get_file(file_idx)
            logging_usage.append([func_name, file_path, has_logging])
        
        return logging_usage
    
    def _expand_global_vars(self) -> list[list]:
        """
        Expand global variables array.
        
        Format: [var_name, file_path, has_type_hint]
        """
        global_vars = []
        vars_data = self.tech_index.get("globalvars", [])
        
        for var_data in vars_data:
            var_name_idx, file_idx, has_type_hint = var_data
            var_name = self._get_name(var_name_idx)
            file_path = self._get_file(file_idx)
            global_vars.append([var_name, file_path, has_type_hint])
        
        return global_vars
    
    def _expand_class_deps(self) -> list[list]:
        """
        Expand class dependencies array.
        
        Format: [class_name, file_path, uses_di]
        """
        class_deps = []
        deps_data = self.tech_index.get("classdeps", [])
        
        for dep_data in deps_data:
            class_name_idx, file_idx, uses_di = dep_data
            class_name = self._get_name(class_name_idx)
            file_path = self._get_file(file_idx)
            class_deps.append([class_name, file_path, uses_di])
        
        return class_deps
    
    def _expand_docstring_formats(self) -> list[list]:
        """
        Expand docstring formats array.
        
        Format: [func_name, format_name]
        format_name: "numpy", "google", "sphinx", "none"
        """
        docstring_formats = []
        formats_data = self.tech_index.get("docstringformats", [])
        functions_data = self.tech_index.get("functions", [])
        
        format_names = ["numpy", "google", "sphinx", "none"]
        
        for format_data in formats_data:
            func_idx, format_type = format_data
            
            if func_idx < len(functions_data):
                func_name_idx = functions_data[func_idx][0]
                func_name = self._get_name(func_name_idx)
            else:
                func_name = "unknown"
            
            format_name = format_names[format_type] if format_type < len(format_names) else "unknown"
            docstring_formats.append([func_name, format_name])
        
        return docstring_formats
    
    def _expand_test_coverage(self) -> list[list]:
        """
        Expand test coverage array.
        
        Format: [func_name, has_test]
        """
        test_coverage = []
        coverage_data = self.tech_index.get("testcoverage", [])
        
        for cov_data in coverage_data:
            func_name_idx, has_test = cov_data
            func_name = self._get_name(func_name_idx)
            test_coverage.append([func_name, has_test])
        
        return test_coverage
    
    def _get_name(self, idx: Optional[int]) -> str:
        """Get name by index."""
        if idx is None or idx < 0 or idx >= len(self.names):
            return "unknown"
        return self.names[idx]
    
    def _get_file(self, idx: int) -> str:
        """Get file path by index."""
        if idx < 0 or idx >= len(self.files):
            return "unknown"
        return self.files[idx]
    
    def _get_default(self, idx: int) -> str:
        """Get default value by index."""
        if idx < 0 or idx >= len(self.defaults):
            return "unknown"
        return self.defaults[idx]
