#!/usr/bin/env python3
"""
TECH-INDEX-PY v3.0 Generator

Генератор компактных индексных файлов Python проектов для AI

ИСПРАВЛЕНИЯ в v3.0:
- ✅ Добавлен парсинг импортов (import/from...import)
- ✅ Добавлен парсинг атрибутов классов
- ✅ Полный парсинг параметров (*args, **kwargs, keyword-only, positional-only)
- ✅ Улучшенный парсинг type annotations (Union, |, module.Type)
- ✅ Поддержка сложных декораторов @decorator(args)
- ✅ Fallback кодировок (UTF-8, CP1251, Latin-1)
- ✅ Валидация путей и создание директорий
- ✅ Хеширование объектов (classes, functions)

Использование:
    python tech_index_generator_v3.py <project_path> <output_path> [options]

Опции:
    --format=json.gz     Формат: json, json.gz, msgpack (по умолчанию json)
    --compress-names     Сжимать массив names с GZIP+Base64
    --hash-len=16        Длина хешей: 8, 16, 32, 64

Примеры:
    python tech_index_generator_v3.py "/path/to/project" "/path/to/output"
    python tech_index_generator_v3.py "D:\\Project" "D:\\Indexes" --format=json.gz
"""

import ast
import json
import hashlib
import os
import sys
import base64
import zlib
import gzip
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import argparse

# MessagePack опционален
try:
    import msgpack
    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False


class TechIndexGeneratorV3:
    """Генератор TECH-INDEX-PY v3.0 с полными исправлениями"""

    def __init__(self, project_root: str, output_dir: str,
                 compress_names: bool = False,
                 hash_len: int = 16,
                 output_format: str = "json"):

        self.project_root = Path(project_root).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.compress_names = compress_names
        self.hash_len = hash_len
        self.output_format = output_format.lower()

        # Валидация формата
        valid_formats = ["json", "json.gz", "msgpack"]
        if self.output_format not in valid_formats:
            raise ValueError(f"Неверный формат: {self.output_format}. Допустимые: {valid_formats}")

        if self.output_format == "msgpack" and not HAS_MSGPACK:
            raise ImportError("Формат msgpack требует: pip install msgpack")

        # Структуры данных
        self.names: List[str] = []
        self.names_index: Dict[str, int] = {}
        self.files: List[str] = []
        self.files_index: Dict[str, int] = {}

        self.modules: List[List[int]] = []
        self.classes: List[List] = []
        self.functions: List[List] = []
        self.parameters: Dict[str, List[List]] = {}
        self.attributes: List[List] = []  # NEW in v3.0
        self.docstrings: List[List[int]] = []
        self.imports: List[List] = []  # FIXED in v3.0

        self.validation = {
            "filehashes": {},
            "objecthashes": {},  # IMPLEMENTED in v3.0
            "integritycheck": {}
        }

        self.location_counter = 1

        # Метаданные v3.0
        self.meta = {
            "version": "3.0",
            "schemaversion": "3.0",
            "indexeddate": datetime.now().isoformat(),
            "sourcehash": "",
            "projectroot": str(self.project_root),
            "pythonversion": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "indexerversion": "v3.0.0",
            "totalobjects": {
                "modules": 0,
                "classes": 0,
                "functions": 0,
                "attributes": 0,  # NEW
                "imports": 0      # FIXED
            },
            "pythonrules": {
                "enforcedpatterns": [],
                "restrictedpatterns": []
            },
            "indexingoptions": {
                "includedocstrings": 1,
                "includecomments": 0,
                "includetypehints": 1,
                "parsedecorators": 1,
                "parselinenumbers": 1
            },
            "compression": {
                "namesencoding": "gzip+base64" if compress_names else "raw",
                "hashlen": hash_len,
                "format": output_format
            }
        }

    def add_to_names(self, name: str) -> int:
        """Добавить имя в справочник"""
        if name in self.names_index:
            return self.names_index[name]
        idx = len(self.names)
        self.names.append(name)
        self.names_index[name] = idx
        return idx

    def add_to_files(self, filepath: str) -> int:
        """Добавить файл в список"""
        if filepath in self.files_index:
            return self.files_index[filepath]
        idx = len(self.files)
        self.files.append(filepath)
        self.files_index[filepath] = idx
        return idx

    def calculate_file_hash(self, filepath: Path) -> str:
        """Вычислить хеш файла"""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()[:self.hash_len]

    def calculate_object_hash(self, obj_data: str) -> str:
        """Вычислить хеш объекта (класса или функции)"""
        sha256 = hashlib.sha256()
        sha256.update(obj_data.encode('utf-8'))
        return sha256.hexdigest()[:self.hash_len]

    def find_python_files(self) -> List[Path]:
        """Найти все Python файлы в проекте"""
        python_files = []
        exclude_dirs = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache', 
                       'node_modules', '.tox', 'build', 'dist', '.eggs'}

        for root, dirs, files in os.walk(self.project_root):
            # Исключить директории
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)

        return sorted(python_files)

    def parse_file(self, filepath: Path) -> Optional[ast.Module]:
        """
        Парсить Python файл с fallback кодировок
        FIXED in v3.0: Поддержка UTF-8, CP1251, Latin-1
        """
        encodings = ['utf-8', 'cp1251', 'latin-1']

        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    source = f.read()

                try:
                    return ast.parse(source, filename=str(filepath))
                except SyntaxError as e:
                    print(f"⚠ Синтаксическая ошибка в {filepath}: {e}")
                    return None

            except UnicodeDecodeError:
                if encoding == encodings[-1]:
                    print(f"⚠ Не удалось прочитать {filepath} (все кодировки)")
                    return None
                continue
            except Exception as e:
                print(f"⚠ Ошибка парсинга {filepath}: {e}")
                return None

        return None

    def extract_type_annotation(self, annotation) -> Optional[str]:
        """
        Извлечь аннотацию типа
        IMPROVED in v3.0: Поддержка сложных типов
        """
        if annotation is None:
            return None

        # Simple name: int, str, List
        if isinstance(annotation, ast.Name):
            return annotation.id

        # Constant: "literal value"
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)

        # Subscript: List[int], Dict[str, int]
        elif isinstance(annotation, ast.Subscript):
            base = self.extract_type_annotation(annotation.value)
            slice_val = self.extract_type_annotation(annotation.slice)
            if base and slice_val:
                return f"{base}[{slice_val}]"
            return base or "Any"

        # Attribute: module.Type
        elif isinstance(annotation, ast.Attribute):
            value = self.extract_type_annotation(annotation.value)
            if value:
                return f"{value}.{annotation.attr}"
            return annotation.attr

        # Tuple: Union[int, str] in Python <3.10
        elif isinstance(annotation, ast.Tuple):
            elements = [self.extract_type_annotation(elt) for elt in annotation.elts]
            elements = [e for e in elements if e]
            if elements:
                return f"Union[{', '.join(elements)}]"
            return "Any"

        # BinOp: int | str (Python 3.10+)
        elif isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
            left = self.extract_type_annotation(annotation.left)
            right = self.extract_type_annotation(annotation.right)
            if left and right:
                return f"{left} | {right}"
            return left or right or "Any"

        # Index (deprecated in Python 3.9+, but still in some code)
        elif hasattr(ast, 'Index') and isinstance(annotation, ast.Index):
            return self.extract_type_annotation(annotation.value)

        return "Any"

    def extract_default_value(self, value_node) -> Optional[str]:
        """Извлечь значение по умолчанию"""
        if isinstance(value_node, ast.Constant):
            val = value_node.value
            if isinstance(val, str):
                return f'"{val}"'
            return str(val)
        elif isinstance(value_node, ast.Name):
            return value_node.id
        elif isinstance(value_node, ast.List):
            return "[]"
        elif isinstance(value_node, ast.Dict):
            return "{}"
        elif isinstance(value_node, ast.Tuple):
            return "()"
        elif isinstance(value_node, ast.Set):
            return "set()"
        elif isinstance(value_node, (ast.UnaryOp, ast.BinOp)):
            return "..."  # Сложное выражение
        return None

    def get_docstring(self, node) -> Optional[str]:
        """Получить docstring узла"""
        if self.meta["indexingoptions"]["includedocstrings"] == 0:
            return None
        return ast.get_docstring(node)

    def detect_docstring_format(self, docstring: str) -> str:
        """Определить формат docstring"""
        if not docstring:
            return "plain"
        if "Args:" in docstring or "Returns:" in docstring:
            return "google"
        elif "Parameters\n" in docstring or "Returns\n" in docstring:
            return "numpy"
        elif ":param" in docstring or ":return:" in docstring:
            return "rst"
        return "plain"

    def process_decorators(self, decorator_list: List) -> Tuple[List[int], int]:
        """
        Парсить декораторы
        IMPROVED in v3.0: Поддержка сложных декораторов

        Returns: (decorators, func_type_override)
        """
        decorators = []
        func_type_override = -1

        for decorator in decorator_list:
            # Simple: @decorator
            if isinstance(decorator, ast.Name):
                dec_name = decorator.id
                dec_idx = self.add_to_names(dec_name)
                decorators.append(dec_idx)

                # Определить тип функции
                if dec_name == "classmethod":
                    func_type_override = 2
                elif dec_name == "staticmethod":
                    func_type_override = 3
                elif dec_name == "property":
                    func_type_override = 4

            # Call: @decorator(arg1, arg2)
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    dec_name = decorator.func.id
                    # Включить аргументы в имя
                    if decorator.args:
                        args_str = ", ".join([
                            self.extract_default_value(arg) or "..."
                            for arg in decorator.args[:3]  # Ограничить 3 аргументами
                        ])
                        full_name = f"{dec_name}({args_str})"
                    else:
                        full_name = f"{dec_name}()"
                    dec_idx = self.add_to_names(full_name)
                    decorators.append(dec_idx)

                elif isinstance(decorator.func, ast.Attribute):
                    # @module.decorator(args)
                    if isinstance(decorator.func.value, ast.Name):
                        dec_name = f"{decorator.func.value.id}.{decorator.func.attr}"
                        dec_idx = self.add_to_names(dec_name)
                        decorators.append(dec_idx)

            # Attribute: @module.decorator or @name.setter
            elif isinstance(decorator, ast.Attribute):
                if isinstance(decorator.value, ast.Name):
                    dec_name = f"{decorator.value.id}.{decorator.attr}"
                    dec_idx = self.add_to_names(dec_name)
                    decorators.append(dec_idx)

                    # Обработать @property.setter
                    if decorator.attr == "setter":
                        func_type_override = 4  # Как property

        return decorators, func_type_override

    def process_function_parameters(self, node, func_idx: int) -> List[int]:
        """
        Парсить параметры функции
        FIXED in v3.0: Полная поддержка всех типов параметров
        """
        param_indices = []
        params_data = []
        param_idx = 0

        args = node.args

        # 1. Positional-only parameters (Python 3.8+)
        if hasattr(args, 'posonlyargs') and args.posonlyargs:
            for arg in args.posonlyargs:
                param_name_idx = self.add_to_names(arg.arg)
                param_type = self.extract_type_annotation(arg.annotation)
                param_type_idx = self.add_to_names(param_type) if param_type else -1

                params_data.append([param_idx, param_name_idx, param_type_idx, 
                                  -1, 4, 1])  # paramtype=4, required
                param_indices.append(param_idx)
                param_idx += 1

        # 2. Regular positional/keyword parameters
        defaults_offset = len(args.args) - len(args.defaults)
        for i, arg in enumerate(args.args):
            param_name_idx = self.add_to_names(arg.arg)
            param_type = self.extract_type_annotation(arg.annotation)
            param_type_idx = self.add_to_names(param_type) if param_type else -1

            default_idx = -1
            is_required = 1

            default_i = i - defaults_offset
            if default_i >= 0 and default_i < len(args.defaults):
                default_value = self.extract_default_value(args.defaults[default_i])
                if default_value:
                    default_idx = self.add_to_names(default_value)
                    is_required = 0

            params_data.append([param_idx, param_name_idx, param_type_idx, 
                              default_idx, 0, is_required])  # paramtype=0
            param_indices.append(param_idx)
            param_idx += 1

        # 3. *args (vararg)
        if args.vararg:
            param_name_idx = self.add_to_names(args.vararg.arg)
            param_type = self.extract_type_annotation(args.vararg.annotation)
            param_type_idx = self.add_to_names(param_type) if param_type else -1

            params_data.append([param_idx, param_name_idx, param_type_idx, 
                              -1, 2, 0])  # paramtype=2, not required
            param_indices.append(param_idx)
            param_idx += 1

        # 4. Keyword-only parameters
        for i, arg in enumerate(args.kwonlyargs):
            param_name_idx = self.add_to_names(arg.arg)
            param_type = self.extract_type_annotation(arg.annotation)
            param_type_idx = self.add_to_names(param_type) if param_type else -1

            default_idx = -1
            is_required = 1

            if i < len(args.kw_defaults) and args.kw_defaults[i] is not None:
                default_value = self.extract_default_value(args.kw_defaults[i])
                if default_value:
                    default_idx = self.add_to_names(default_value)
                    is_required = 0

            params_data.append([param_idx, param_name_idx, param_type_idx, 
                              default_idx, 1, is_required])  # paramtype=1
            param_indices.append(param_idx)
            param_idx += 1

        # 5. **kwargs (kwarg)
        if args.kwarg:
            param_name_idx = self.add_to_names(args.kwarg.arg)
            param_type = self.extract_type_annotation(args.kwarg.annotation)
            param_type_idx = self.add_to_names(param_type) if param_type else -1

            params_data.append([param_idx, param_name_idx, param_type_idx, 
                              -1, 3, 0])  # paramtype=3, not required
            param_indices.append(param_idx)
            param_idx += 1

        if params_data:
            self.parameters[str(func_idx)] = params_data

        return param_indices

    def process_function(self, node, module_idx: int, class_idx: int = -1) -> int:
        """Обработать функцию/метод"""
        func_idx = len(self.functions)
        name_idx = self.add_to_names(node.name)

        # Определить тип функции
        func_type_idx = 0
        if isinstance(node, ast.AsyncFunctionDef):
            func_type_idx = 1

        # Парсить декораторы
        decorators, func_type_override = self.process_decorators(node.decorator_list)
        if func_type_override >= 0:
            func_type_idx = func_type_override

        # Тип возврата
        return_type = self.extract_type_annotation(node.returns)
        return_idx = self.add_to_names(return_type) if return_type else -1

        # Параметры
        param_indices = self.process_function_parameters(node, func_idx)

        # Location
        location_id = self.location_counter
        self.location_counter += 1

        self.functions.append([module_idx, class_idx, name_idx, func_type_idx, 
                              return_idx, param_indices, decorators, location_id])

        # Docstring
        docstring = self.get_docstring(node)
        if docstring:
            doc_format = self.detect_docstring_format(docstring)
            doc_idx = self.add_to_names(docstring)
            format_idx = self.add_to_names(doc_format)
            self.docstrings.append([2, func_idx, doc_idx, format_idx])

        return func_idx

    def process_class_attributes(self, node: ast.ClassDef, class_idx: int) -> List[int]:
        """
        Парсить атрибуты класса
        NEW in v3.0
        """
        attributes = []

        for item in node.body:
            # x: int = 5 (annotated assignment)
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                attr_name_idx = self.add_to_names(item.target.id)
                attr_type = self.extract_type_annotation(item.annotation)
                attr_type_idx = self.add_to_names(attr_type) if attr_type else -1

                default_idx = -1
                if item.value:
                    default_value = self.extract_default_value(item.value)
                    if default_value:
                        default_idx = self.add_to_names(default_value)

                location_id = self.location_counter
                self.location_counter += 1

                attr_idx = len(self.attributes)
                self.attributes.append([class_idx, attr_name_idx, attr_type_idx, 
                                       default_idx, location_id])
                attributes.append(attr_idx)

            # x = 5 (regular assignment)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attr_name_idx = self.add_to_names(target.id)

                        default_idx = -1
                        if item.value:
                            default_value = self.extract_default_value(item.value)
                            if default_value:
                                default_idx = self.add_to_names(default_value)

                        location_id = self.location_counter
                        self.location_counter += 1

                        attr_idx = len(self.attributes)
                        self.attributes.append([class_idx, attr_name_idx, -1, 
                                               default_idx, location_id])
                        attributes.append(attr_idx)

        return attributes

    def process_class(self, node: ast.ClassDef, module_idx: int) -> int:
        """Обработать класс"""
        class_idx = len(self.classes)
        name_idx = self.add_to_names(node.name)

        # Базовые классы
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_idx = self.add_to_names(base.id)
                base_classes.append(base_idx)
            elif isinstance(base, ast.Attribute):
                base_name = f"{base.value.id}.{base.attr}" if isinstance(base.value, ast.Name) else base.attr
                base_idx = self.add_to_names(base_name)
                base_classes.append(base_idx)

        # Методы
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_idx = self.process_function(item, module_idx, class_idx)
                methods.append(method_idx)

        # Атрибуты (NEW in v3.0)
        attributes = self.process_class_attributes(node, class_idx)

        location_id = self.location_counter
        self.location_counter += 1

        # Изменено: добавлен 7-й элемент attributes
        self.classes.append([module_idx, name_idx, 0, base_classes, methods, 
                            location_id, attributes])

        # Docstring
        docstring = self.get_docstring(node)
        if docstring:
            doc_format = self.detect_docstring_format(docstring)
            doc_idx = self.add_to_names(docstring)
            format_idx = self.add_to_names(doc_format)
            self.docstrings.append([1, class_idx, doc_idx, format_idx])

        return class_idx

    def process_imports(self, tree: ast.Module, module_idx: int):
        """
        Парсить импорты
        NEW in v3.0 - КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ
        """
        for node in tree.body:
            if isinstance(node, ast.Import):
                # import module
                for alias in node.names:
                    target_idx = self.add_to_names(alias.name)
                    self.imports.append([module_idx, target_idx, [], 0, 0])

            elif isinstance(node, ast.ImportFrom):
                # from module import ...
                module_name = node.module or ""
                if module_name:
                    target_idx = self.add_to_names(module_name)
                else:
                    target_idx = -1

                imported = [self.add_to_names(a.name) for a in node.names]
                level = node.level or 0
                self.imports.append([module_idx, target_idx, imported, 1, level])

    def process_module(self, filepath: Path, tree: ast.Module) -> int:
        """Обработать модуль"""
        module_idx = len(self.modules)

        rel_path = filepath.relative_to(self.project_root)
        module_name = str(rel_path.with_suffix('')).replace(os.sep, '.')

        name_idx = self.add_to_names(module_name)
        file_idx = self.add_to_files(str(rel_path))

        location_id = self.location_counter
        self.location_counter += 1

        self.modules.append([name_idx, file_idx, location_id])

        # Хеш файла
        file_hash = self.calculate_file_hash(filepath)
        self.validation["filehashes"][str(file_idx)] = file_hash

        # Парсить импорты (NEW in v3.0)
        self.process_imports(tree, module_idx)

        # Парсить содержимое
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self.process_class(node, module_idx)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.process_function(node, module_idx)

        # Docstring модуля
        docstring = self.get_docstring(tree)
        if docstring:
            doc_format = self.detect_docstring_format(docstring)
            doc_idx = self.add_to_names(docstring)
            format_idx = self.add_to_names(doc_format)
            self.docstrings.append([0, module_idx, doc_idx, format_idx])

        return module_idx

    def generate_object_hashes(self):
        """
        Генерировать хеши объектов
        IMPLEMENTED in v3.0
        """
        # Хеши классов
        for idx, cls in enumerate(self.classes):
            class_name = self.names[cls[1]]
            base_classes = [self.names[b] for b in cls[3]]
            methods = [self.names[self.functions[m][2]] for m in cls[4]]
            attributes = [self.names[self.attributes[a][1]] for a in cls[6]] if len(cls) > 6 else []

            obj_str = f"class:{class_name}:bases:{base_classes}:methods:{methods}:attrs:{attributes}"
            obj_hash = self.calculate_object_hash(obj_str)
            self.validation["objecthashes"][f"c{idx}"] = obj_hash

        # Хеши функций
        for idx, func in enumerate(self.functions):
            func_name = self.names[func[2]]
            return_type = self.names[func[4]] if func[4] >= 0 else "None"

            params = []
            if str(idx) in self.parameters:
                for param in self.parameters[str(idx)]:
                    param_name = self.names[param[1]]
                    param_type = self.names[param[2]] if param[2] >= 0 else "Any"
                    params.append(f"{param_name}:{param_type}")

            obj_str = f"func:{func_name}:params:{params}:return:{return_type}"
            obj_hash = self.calculate_object_hash(obj_str)
            self.validation["objecthashes"][f"f{idx}"] = obj_hash

    def compress_names_array(self) -> str:
        """Сжать массив names"""
        names_json = json.dumps(self.names, ensure_ascii=False)
        compressed = zlib.compress(names_json.encode('utf-8'), level=9)
        return base64.b64encode(compressed).decode('ascii')

    def generate_index(self) -> Dict:
        """Генерировать индекс"""
        print(f"🔍 Сканирование: {self.project_root}")

        python_files = self.find_python_files()
        print(f"📁 Найдено файлов: {len(python_files)}")

        # Предзаполнить стандартные имена
        self.add_to_names("EXPLICITIMPORTSONLY")
        self.add_to_names("NOCIRCULARIMPORTS")
        self.add_to_names("NOMETACLASSES")
        self.add_to_names("plain")
        self.add_to_names("google")
        self.add_to_names("numpy")
        self.add_to_names("rst")
        sha256_idx = self.add_to_names("sha256")

        # Парсить файлы
        for i, filepath in enumerate(python_files, 1):
            print(f"  [{i}/{len(python_files)}] {filepath.name}")
            tree = self.parse_file(filepath)
            if tree:
                self.process_module(filepath, tree)

        # Обновить счетчики
        self.meta["totalobjects"]["modules"] = len(self.modules)
        self.meta["totalobjects"]["classes"] = len(self.classes)
        self.meta["totalobjects"]["functions"] = len(self.functions)
        self.meta["totalobjects"]["attributes"] = len(self.attributes)
        self.meta["totalobjects"]["imports"] = len(self.imports)

        # Генерировать хеши объектов
        print("🔐 Генерация хешей объектов...")
        self.generate_object_hashes()

        # Хеш проекта
        all_hashes = ''.join(self.validation["filehashes"].values())
        project_hash = hashlib.sha256(all_hashes.encode()).hexdigest()
        self.meta["sourcehash"] = project_hash[:self.hash_len]

        # Integrity check
        self.validation["integritycheck"]["algorithmidx"] = sha256_idx

        # Собрать индекс
        index = {
            "meta": self.meta,
            "names": self.names,
            "files": self.files,
            "modules": self.modules,
            "classes": self.classes,
            "functions": self.functions,
            "parameters": self.parameters,
            "attributes": self.attributes,  # NEW
            "docstrings": self.docstrings,
            "validation": self.validation,
            "imports": self.imports  # FIXED
        }

        if self.compress_names:
            print("📦 Сжатие массива names...")
            index["names"] = self.compress_names_array()

        # Вычислить integrity hash
        index_json = json.dumps(index, sort_keys=True, separators=(',', ':'))
        index_hash = hashlib.sha256(index_json.encode()).hexdigest()
        index["validation"]["integritycheck"]["datahash"] = index_hash[:self.hash_len]

        return index

    def save_index(self, index: Dict):
        """Сохранить индекс"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        project_name = self.project_root.name

        # Выбор расширения
        extensions = {
            "json": ".json",
            "json.gz": ".json.gz",
            "msgpack": ".msgpack"
        }

        ext = extensions[self.output_format]
        output_file = self.output_dir / f"tech-index-py-{project_name}-v3{ext}"

        # Сохранение
        if self.output_format == "json":
            # Minified JSON
            json_data = json.dumps(index, separators=(',', ':'), ensure_ascii=False)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_data)

        elif self.output_format == "json.gz":
            # Minified JSON + GZIP
            json_data = json.dumps(index, separators=(',', ':'), ensure_ascii=False)
            with gzip.open(output_file, 'wb', compresslevel=9) as f:
                f.write(json_data.encode('utf-8'))

        elif self.output_format == "msgpack":
            # MessagePack
            with open(output_file, 'wb') as f:
                msgpack.pack(index, f, use_bin_type=True)

        file_size = output_file.stat().st_size

        print(f"\n✅ Индекс сохранен: {output_file}")
        print(f"📊 Размер: {file_size:,} байт ({file_size/1024:.1f} КБ)")
        print(f"\n📈 Статистика:")
        print(f"   Модулей: {self.meta['totalobjects']['modules']}")
        print(f"   Классов: {self.meta['totalobjects']['classes']}")
        print(f"   Функций: {self.meta['totalobjects']['functions']}")
        print(f"   Атрибутов: {self.meta['totalobjects']['attributes']}")
        print(f"   Импортов: {self.meta['totalobjects']['imports']}")
        print(f"   Формат: {self.output_format}")


def validate_paths(args):
    """
    Валидация путей
    NEW in v3.0
    """
    project_path = Path(args.project_path)

    # Валидация project path
    if not project_path.exists():
        print(f"❌ Ошибка: {project_path} не существует")
        sys.exit(1)

    if not project_path.is_dir():
        print(f"❌ Ошибка: {project_path} не является директорией")
        sys.exit(1)

    # Валидация/создание output path
    output_path = Path(args.output_path)

    if output_path.exists() and not output_path.is_dir():
        print(f"❌ Ошибка: {output_path} существует и не является директорией")
        sys.exit(1)

    if not output_path.exists():
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Создана директория: {output_path}")
        except Exception as e:
            print(f"❌ Ошибка создания директории {output_path}: {e}")
            sys.exit(1)

    return project_path, output_path


def main():
    parser = argparse.ArgumentParser(
        description='TECH-INDEX-PY v3.0 - полные исправления',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python tech_index_generator_v3.py "/path/to/project" "/path/to/output"
  python tech_index_generator_v3.py "D:\\Project" "D:\\Output" --format=json.gz
  python tech_index_generator_v3.py "." "./indexes" --hash-len=32
        """
    )

    parser.add_argument('project_path', help='Путь к Python проекту')
    parser.add_argument('output_path', help='Путь к каталогу для индексов')
    parser.add_argument('--format', default='json', choices=['json', 'json.gz', 'msgpack'],
                       help='Формат вывода (по умолчанию: json)')
    parser.add_argument('--compress-names', action='store_true',
                       help='Сжимать массив names с GZIP+Base64')
    parser.add_argument('--hash-len', type=int, default=16, choices=[8, 16, 32, 64],
                       help='Длина хешей (по умолчанию: 16)')

    args = parser.parse_args()

    # Валидация путей
    project_path, output_path = validate_paths(args)

    print("=" * 70)
    print("TECH-INDEX-PY v3.0 Generator")
    print("=" * 70)

    try:
        generator = TechIndexGeneratorV3(
            str(project_path),
            str(output_path),
            compress_names=args.compress_names,
            hash_len=args.hash_len,
            output_format=args.format
        )

        index = generator.generate_index()
        generator.save_index(index)

        print("\n✨ Готово!")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
