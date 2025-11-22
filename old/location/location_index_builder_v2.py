#!/usr/bin/env python3
"""
TECH-LOCATION Builder v2.0 (Compact)

Генератор компактного индекса физического расположения объектов.
Использует массивы вместо объектов для минимального размера.

Использование:
    python location_index_builder_v2.py <project_path> <tech_index_dir> <output_dir> [options]

Опции:
    --format=json        Формат вывода: json, json.gz (по умолчанию json)
    --minify             Компактный JSON (без отступов и переносов строк)

Примеры:
    python location_index_builder_v2.py "D:\\PROJECT" "D:\\INDEXES" "D:\\INDEXES"
    python location_index_builder_v2.py "." "./idx" "./idx" --format=json.gz
    python location_index_builder_v2.py "." "./idx" "./idx" --minify
"""

import ast
import json
import hashlib
import os
import sys
import gzip
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import argparse


class LocationIndexBuilderV2:
    """Построитель компактного TECH-LOCATION индекса v2.0"""

    def __init__(self, project_root: str, tech_index_path: str, output_format: str = "json", minify: bool = False):
        self.project_root = Path(project_root).resolve()
        self.tech_index_path = Path(tech_index_path).resolve()
        self.output_format = output_format.lower()
        self.minify = minify

        # Загрузить TECH-INDEX
        self.tech_index = self._load_tech_index()

        # Компактные массивы (индексация строк)
        self.paths: List[str] = []
        self.paths_index: Dict[str, int] = {}

        self.modifieds: List[str] = []
        self.modifieds_index: Dict[str, int] = {}

        self.hashes: List[str] = []
        self.hashes_index: Dict[str, int] = {}

        self.decorators: List[str] = []
        self.decorators_index: Dict[str, int] = {}

        self.commenttexts: List[str] = []
        self.commenttexts_index: Dict[str, int] = {}

        # Компактные массивы (данные)
        self.files: List[List[int]] = []
        self.modules: List[List[int]] = []
        self.classes: List[List] = []
        self.functions: List[List] = []
        self.imports: List[List[int]] = []
        self.comments: List[List[int]] = []

        # Метаданные
        self.meta = {
            "version": "2.0",
            "schemaversion": "2.0",
            "indexeddate": datetime.now().isoformat(),
            "techindexhash": self._calculate_tech_index_hash(),
            "projectroot": str(self.project_root),
            "techindexpath": str(self.tech_index_path),
            "totalobjects": {
                "modules": 0,
                "classes": 0,
                "functions": 0,
                "imports": 0,
                "comments": 0
            }
        }

        # Типы комментариев
        self.comment_types = {
            "TODO": 0, "FIXME": 1, "NOTE": 2, "WARNING": 3,
            "HACK": 4, "XXX": 5, "OPTIMIZE": 6
        }

        # Паттерны комментариев (с IGNORECASE для поиска в любом регистре)
        self.comment_patterns = {
            "TODO": re.compile(r'#\s*TODO[:\s](.*)', re.IGNORECASE),
            "FIXME": re.compile(r'#\s*FIXME[:\s](.*)', re.IGNORECASE),
            "NOTE": re.compile(r'#\s*NOTE[:\s](.*)', re.IGNORECASE),
            "WARNING": re.compile(r'#\s*WARNING[:\s](.*)', re.IGNORECASE),
            "HACK": re.compile(r'#\s*HACK[:\s](.*)', re.IGNORECASE),
            "XXX": re.compile(r'#\s*XXX[:\s](.*)', re.IGNORECASE),
            "OPTIMIZE": re.compile(r'#\s*OPTIMIZE[:\s](.*)', re.IGNORECASE)
        }

    def _add_to_array(self, value: str, array: List[str], index: Dict[str, int]) -> int:
        """Добавить значение в массив с дедупликацией"""
        if value in index:
            return index[value]
        idx = len(array)
        array.append(value)
        index[value] = idx
        return idx

    def _load_tech_index(self) -> Dict:
        """Загрузить TECH-INDEX"""
        if not self.tech_index_path.exists():
            raise FileNotFoundError(f"TECH-INDEX не найден: {self.tech_index_path}")

        print(f"📖 Загрузка TECH-INDEX: {self.tech_index_path.name}")

        if self.tech_index_path.suffix == '.gz':
            with gzip.open(self.tech_index_path, 'rt', encoding='utf-8') as f:
                return json.load(f)
        else:
            with open(self.tech_index_path, 'r', encoding='utf-8') as f:
                return json.load(f)

    def _calculate_tech_index_hash(self) -> str:
        """Вычислить SHA256 хеш TECH-INDEX"""
        sha256 = hashlib.sha256()

        if self.tech_index_path.suffix == '.gz':
            with gzip.open(self.tech_index_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
        else:
            with open(self.tech_index_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)

        return sha256.hexdigest()[:16]

    def _calculate_file_hash(self, filepath: Path) -> str:
        """Вычислить SHA256 хеш файла"""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()[:16]

    def _process_file_info(self, file_id: int) -> int:
        """Обработать информацию о файле, вернуть индекс"""
        file_path_rel = self.tech_index["files"][file_id]
        file_path = self.project_root / file_path_rel

        if not file_path.exists():
            print(f"⚠ Файл не найден: {file_path_rel}")
            return -1

        stat = file_path.stat()

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Добавить в индексы
        path_idx = self._add_to_array(file_path_rel, self.paths, self.paths_index)

        modified_str = datetime.fromtimestamp(stat.st_mtime).isoformat()
        modified_idx = self._add_to_array(modified_str, self.modifieds, self.modifieds_index)

        file_hash = self._calculate_file_hash(file_path)
        hash_idx = self._add_to_array(file_hash, self.hashes, self.hashes_index)

        # [path_idx, line_count, size_bytes, modified_idx, hash_idx]
        self.files.append([path_idx, len(lines), stat.st_size, modified_idx, hash_idx])

        return len(self.files) - 1

    def _parse_file(self, filepath: Path) -> Tuple[Optional[ast.Module], List[str]]:
        """Парсить файл"""
        encodings = ['utf-8', 'cp1251', 'latin-1']

        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    source = f.read()
                    lines = source.splitlines()

                try:
                    tree = ast.parse(source, filename=str(filepath))
                    return tree, lines
                except SyntaxError:
                    return None, []

            except UnicodeDecodeError:
                if encoding == encodings[-1]:
                    return None, []
                continue
            except Exception:
                return None, []

        return None, []

    def _extract_docstring_coords(self, node) -> Optional[List[int]]:
        """Извлечь координаты docstring [line_start, line_end]"""
        if not node.body:
            return None

        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            if isinstance(first.value.value, str):
                return [first.lineno, first.end_lineno]

        return None

    def _extract_decorators_compact(self, node) -> List[List[int]]:
        """Извлечь декораторы [[line, decorator_idx], ...]"""
        decorators = []

        for dec in node.decorator_list:
            dec_str = ""

            if isinstance(dec, ast.Name):
                dec_str = f"@{dec.id}"
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Name):
                    dec_str = f"@{dec.func.id}(...)"
                elif isinstance(dec.func, ast.Attribute):
                    if isinstance(dec.func.value, ast.Name):
                        dec_str = f"@{dec.func.value.id}.{dec.func.attr}"
            elif isinstance(dec, ast.Attribute):
                if isinstance(dec.value, ast.Name):
                    dec_str = f"@{dec.value.id}.{dec.attr}"

            if dec_str:
                dec_idx = self._add_to_array(dec_str, self.decorators, self.decorators_index)
                decorators.append([dec.lineno, dec_idx])

        return decorators

    def _find_body_start(self, node, docstring_coords: Optional[List[int]]) -> int:
        """Найти начало тела"""
        if docstring_coords:
            return docstring_coords[1] + 1

        if node.body:
            return node.body[0].lineno

        return node.lineno + 1

    def _get_indentation(self, lines: List[str], line_num: int) -> int:
        """Получить уровень отступа"""
        if 0 <= line_num - 1 < len(lines):
            line = lines[line_num - 1]
            return len(line) - len(line.lstrip())
        return 0

    def _extract_comments(self, file_id: int, lines: List[str]):
        """Извлечь важные комментарии (регистронезависимый поиск)"""
        for line_num, line in enumerate(lines, 1):
            for comment_type, pattern in self.comment_patterns.items():
                match = pattern.search(line)
                if match:
                    content = match.group(1).strip()
                    type_idx = self.comment_types[comment_type]
                    content_idx = self._add_to_array(content, self.commenttexts, 
                                                     self.commenttexts_index)

                    # [file_id, line, type_idx, content_idx]
                    self.comments.append([file_id, line_num, type_idx, content_idx])

    def _process_module(self, module_idx: int, tree: ast.Module, file_id: int):
        """Обработать модуль"""
        module_data = self.tech_index["modules"][module_idx]
        location_id = module_data[2]

        # Получить количество строк из files
        file_info = self.files[file_id]
        line_count = file_info[1]  # line_count

        docstring_coords = self._extract_docstring_coords(tree)

        # [module_id, location_id, file_id, line_start, line_end, docstring?]
        module_entry = [module_idx, location_id, file_id, 1, line_count]

        if docstring_coords:
            module_entry.append(docstring_coords)

        self.modules.append(module_entry)

    def _process_class(self, class_idx: int, node: ast.ClassDef, file_id: int, lines: List[str]):
        """Обработать класс"""
        class_data = self.tech_index["classes"][class_idx]
        location_id = class_data[5]

        decorators = self._extract_decorators_compact(node)
        line_start = decorators[0][0] if decorators else node.lineno
        line_end = node.end_lineno

        docstring_coords = self._extract_docstring_coords(node)
        body_start = self._find_body_start(node, docstring_coords)
        indentation = self._get_indentation(lines, node.lineno)

        # [class_id, location_id, file_id, line_start, line_end, definition_line, 
        #  body_start, indentation, decorators?, docstring?]
        class_entry = [class_idx, location_id, file_id, line_start, line_end, 
                      node.lineno, body_start, indentation]

        if decorators:
            class_entry.append(decorators)

        if docstring_coords:
            if len(class_entry) == 8:
                class_entry.append([])
            class_entry.append(docstring_coords)

        self.classes.append(class_entry)

    def _process_function(self, func_idx: int, node, file_id: int, lines: List[str]):
        """Обработать функцию"""
        func_data = self.tech_index["functions"][func_idx]
        location_id = func_data[7]

        decorators = self._extract_decorators_compact(node)
        line_start = decorators[0][0] if decorators else node.lineno
        line_end = node.end_lineno

        docstring_coords = self._extract_docstring_coords(node)
        body_start = self._find_body_start(node, docstring_coords)
        indentation = self._get_indentation(lines, node.lineno)

        # [function_id, location_id, file_id, line_start, line_end, signature_line,
        #  body_start, indentation, decorators?, docstring?]
        func_entry = [func_idx, location_id, file_id, line_start, line_end,
                     node.lineno, body_start, indentation]

        if decorators:
            func_entry.append(decorators)

        if docstring_coords:
            if len(func_entry) == 8:
                func_entry.append([])
            func_entry.append(docstring_coords)

        self.functions.append(func_entry)

    def _process_imports(self, tree: ast.Module, file_id: int):
        """Обработать импорты"""
        import_idx = len(self.imports)

        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # [import_id, file_id, line, type] type: 0=import
                    self.imports.append([import_idx, file_id, node.lineno, 0])
                    import_idx += 1

            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    # [import_id, file_id, line, type] type: 1=from_import
                    self.imports.append([import_idx, file_id, node.lineno, 1])
                    import_idx += 1

    def _process_file(self, file_id: int):
        """Обработать файл"""
        file_path_rel = self.tech_index["files"][file_id]
        file_path = self.project_root / file_path_rel

        if not file_path.exists():
            return

        tree, lines = self._parse_file(file_path)
        if not tree:
            return

        # Комментарии (регистронезависимый поиск)
        self._extract_comments(file_id, lines)

        # Импорты
        self._process_imports(tree, file_id)

        # Модули
        for module_idx, module_data in enumerate(self.tech_index["modules"]):
            if module_data[1] == file_id:
                self._process_module(module_idx, tree, file_id)

        # Классы и функции
        self._process_ast_node(tree, file_id, lines)

    def _process_ast_node(self, node, file_id: int, lines: List[str]):
        """Рекурсивно обработать AST"""
        for item in node.body if hasattr(node, 'body') else []:
            if isinstance(item, ast.ClassDef):
                for class_idx, class_data in enumerate(self.tech_index["classes"]):
                    class_name_idx = class_data[1]
                    class_name = self.tech_index["names"][class_name_idx]

                    if class_name == item.name:
                        if not any(c[0] == class_idx for c in self.classes):
                            self._process_class(class_idx, item, file_id, lines)

                            # Методы
                            for method in item.body:
                                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                    for func_idx, func_data in enumerate(self.tech_index["functions"]):
                                        func_class_idx = func_data[1]
                                        func_name_idx = func_data[2]
                                        func_name = self.tech_index["names"][func_name_idx]

                                        if func_class_idx == class_idx and func_name == method.name:
                                            if not any(f[0] == func_idx for f in self.functions):
                                                self._process_function(func_idx, method, file_id, lines)
                        break

            elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for func_idx, func_data in enumerate(self.tech_index["functions"]):
                    func_class_idx = func_data[1]
                    func_name_idx = func_data[2]
                    func_name = self.tech_index["names"][func_name_idx]

                    if func_class_idx == -1 and func_name == item.name:
                        if not any(f[0] == func_idx for f in self.functions):
                            self._process_function(func_idx, item, file_id, lines)
                        break

    def build(self):
        """Построить индекс"""
        print(f"🔍 Построение TECH-LOCATION v2.0 для: {self.project_root}")

        files = self.tech_index["files"]
        total_files = len(files)

        # Обработать файлы
        for file_id in range(total_files):
            print(f"  [{file_id + 1}/{total_files}] {files[file_id]}")
            self._process_file_info(file_id)
            self._process_file(file_id)

        # Обновить счетчики
        self.meta["totalobjects"]["modules"] = len(self.modules)
        self.meta["totalobjects"]["classes"] = len(self.classes)
        self.meta["totalobjects"]["functions"] = len(self.functions)
        self.meta["totalobjects"]["imports"] = len(self.imports)
        self.meta["totalobjects"]["comments"] = len(self.comments)

        print(f"\n✅ Обработано:")
        print(f"   Модулей: {len(self.modules)}")
        print(f"   Классов: {len(self.classes)}")
        print(f"   Функций: {len(self.functions)}")
        print(f"   Импортов: {len(self.imports)}")
        print(f"   Комментариев: {len(self.comments)}")

    def save(self, output_path: Path):
        """Сохранить индекс"""
        output_path.mkdir(parents=True, exist_ok=True)

        project_name = self.project_root.name
        ext = ".json.gz" if self.output_format == "json.gz" else ".json"
        output_file = output_path / f"tech-location-{project_name}-v2{ext}"

        # Собрать индекс
        location_index = {
            "meta": self.meta,
            "paths": self.paths,
            "modifieds": self.modifieds,
            "hashes": self.hashes,
            "decorators": self.decorators,
            "commenttexts": self.commenttexts,
            "files": self.files,
            "modules": self.modules,
            "classes": self.classes,
            "functions": self.functions,
            "imports": self.imports,
            "comments": self.comments
        }

        # Сохранить
        if self.output_format == "json":
            if self.minify:
                # Минифицированный JSON (без отступов)
                json_data = json.dumps(location_index, separators=(',', ':'), ensure_ascii=False)
            else:
                # Форматированный JSON (с отступами)
                json_data = json.dumps(location_index, indent=2, ensure_ascii=False)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(json_data)
        else:
            # GZIP всегда минифицированный
            json_data = json.dumps(location_index, separators=(',', ':'), ensure_ascii=False)
            with gzip.open(output_file, 'wb', compresslevel=9) as f:
                f.write(json_data.encode('utf-8'))

        file_size = output_file.stat().st_size

        print(f"\n✅ TECH-LOCATION v2.0 сохранен: {output_file}")
        print(f"📊 Размер: {file_size:,} байт ({file_size/1024:.1f} КБ)")


def find_tech_index(index_dir: Path, project_name: str) -> Optional[Path]:
    """Найти TECH-INDEX"""
    patterns = [
        f"tech-index-py-{project_name}-v3.json",
        f"tech-index-py-{project_name}-v3.json.gz"
    ]

    for pattern in patterns:
        index_file = index_dir / pattern
        if index_file.exists():
            return index_file

    for file in index_dir.glob("tech-index-py-*-v3.json*"):
        return file

    return None


def main():
    parser = argparse.ArgumentParser(description='TECH-LOCATION Builder v2.0 (Compact)')

    parser.add_argument('project_path', help='Путь к проекту')
    parser.add_argument('tech_index_dir', help='Директория с TECH-INDEX')
    parser.add_argument('output_dir', help='Директория для TECH-LOCATION')
    parser.add_argument('--format', default='json', choices=['json', 'json.gz'],
                       help='Формат вывода')
    parser.add_argument('--minify', action='store_true',
                       help='Минифицированный JSON (без отступов)')

    args = parser.parse_args()

    project_path = Path(args.project_path).resolve()
    tech_index_dir = Path(args.tech_index_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not project_path.exists():
        print(f"❌ Проект не найден: {project_path}")
        sys.exit(1)

    if not tech_index_dir.exists():
        print(f"❌ Директория с индексами не найдена: {tech_index_dir}")
        sys.exit(1)

    project_name = project_path.name
    tech_index_file = find_tech_index(tech_index_dir, project_name)

    if not tech_index_file:
        print(f"❌ TECH-INDEX не найден в {tech_index_dir}")
        sys.exit(1)

    print("=" * 70)
    print("TECH-LOCATION Builder v2.0 (Compact)")
    print("=" * 70)
    print(f"📁 Проект: {project_path}")
    print(f"📋 TECH-INDEX: {tech_index_file.name}")
    print(f"💾 Вывод: {output_dir}")
    print(f"📝 Формат: {args.format}" + (" (minified)" if args.minify else ""))
    print("=" * 70)

    try:
        builder = LocationIndexBuilderV2(
            str(project_path),
            str(tech_index_file),
            output_format=args.format,
            minify=args.minify
        )

        builder.build()
        builder.save(output_dir)

        print("\n✨ Готово!")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
