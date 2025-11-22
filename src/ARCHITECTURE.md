# Архитектура PY-Indexer v3.0

## Обзор системы

PY-Indexer v3.0 - модульная система для генерации компактных индексов Python проектов.

### Цели проекта

1. Генерация максимально компактных индексов для AI-анализа
2. Поддержка двух форматов: TECH-INDEX (компактный) и TECH-LOCATION (развернутый)
3. Расширенный анализ кода с проверкой правил кодирования
4. Модульная архитектура с четким разделением ответственности

### Основные компоненты

```
┌─────────────┐
│   CLI       │ - Интерфейс командной строки
└──────┬──────┘
       │
┌──────▼──────┐
│  Validator  │ - Валидация входных данных
└──────┬──────┘
       │
┌──────▼──────┐
│   Parser    │ - AST парсинг Python файлов
└──────┬──────┘
       │
┌──────▼──────┐
│  Indexer    │ - Индексация и анализ кода
└──────┬──────┘
       │
┌──────▼──────┐
│  Builder    │ - Построение индексов (TECH-INDEX / TECH-LOCATION)
└──────┬──────┘
       │
┌──────▼──────┐
│ Serializer  │ - Сериализация (JSON / JSON.gz / MessagePack)
└──────┬──────┘
       │
┌──────▼──────┐
│   Output    │ - Файлы индексов
└─────────────┘
```

---

## Модули и их ответственность

### 1. parser.py - AST Парсер

**Ответственность:**
- Парсинг Python файлов в AST
- Извлечение модулей, классов, функций
- Извлечение импортов
- Извлечение декораторов
- Извлечение docstrings
- Извлечение комментариев

**Публичный API:**
```python
class ASTParser:
    def parse_file(self, file_path: str) -> ParsedFile
    def extract_imports(self, tree: ast.Module) -> list[Import]
    def extract_classes(self, tree: ast.Module) -> list[ClassDef]
    def extract_functions(self, tree: ast.Module) -> list[FunctionDef]
    def extract_type_hints(self, node: ast.FunctionDef) -> TypeHints
```

**Зависимости:**
- `ast` (stdlib)
- `utils_logger.py`
- `utils_file.py`

---

### 2. indexer.py - Индексатор

**Ответственность:**
- Индексация имен (names справочник)
- Индексация файлов
- Индексация default values
- Анализ кода на правила:
  - Mutable defaults
  - SQL-инъекции
  - Hardcoded secrets
  - Global variables
  - Logging usage
  - Type hints presence
  - Docstrings presence

**Публичный API:**
```python
class CodeIndexer:
    def index_names(self, parsed_files: list[ParsedFile]) -> list[str]
    def index_files(self, parsed_files: list[ParsedFile]) -> list[str]
    def detect_mutable_defaults(self, function: FunctionDef) -> list[MutableDefault]
    def detect_sql_injections(self, function: FunctionDef) -> list[SQLInjection]
    def detect_hardcoded_secrets(self, source: str) -> list[HardcodedSecret]
    def detect_global_vars(self, module: ast.Module) -> list[GlobalVar]
```

**Зависимости:**
- `parser.py`
- `utils_logger.py`
- `utils_hash.py`

---

### 3. validator.py - Валидатор

**Ответственность:**
- Валидация входных путей
- Проверка существования файлов
- Проверка прав доступа
- Валидация параметров командной строки

**Публичный API:**
```python
class InputValidator:
    def validate_project_path(self, path: str) -> bool
    def validate_output_path(self, path: str) -> bool
    def validate_format(self, format: str) -> bool
    def validate_hash_length(self, length: int) -> bool
```

**Зависимости:**
- `pathlib` (stdlib)
- `utils_logger.py`

---

### 4. builders/ - Построители индексов

#### builders/builder_tech_index.py

**Ответственность:**
- Построение TECH-INDEX (компактный формат)
- Применение числовых ссылок
- Сжатие массива names (опционально)
- Генерация хешей

**Публичный API:**
```python
class TechIndexBuilder:
    def __init__(self, indexer: CodeIndexer, logger: Logger)
    def build(self, parsed_files: list[ParsedFile]) -> dict
    def compress_names(self, names: list[str]) -> str
```

**Зависимости:**
- `indexer.py`
- `utils_logger.py`
- `utils_hash.py`

#### builders/builder_location.py

**Ответственность:**
- Построение TECH-LOCATION (развернутый формат)
- Использование полных имен вместо индексов
- Человекочитаемый формат

**Публичный API:**
```python
class LocationBuilder:
    def __init__(self, tech_index: dict, logger: Logger)
    def build(self, parsed_files: list[ParsedFile]) -> dict
    def expand_references(self, compact_data: list) -> list
```

**Зависимости:**
- `indexer.py`
- `utils_logger.py`

---

### 5. serializers/ - Сериализаторы

#### serializers/serializer_base.py

**Ответственность:**
- Базовый класс для всех сериализаторов
- Определение интерфейса

**Публичный API:**
```python
class BaseSerializer(ABC):
    @abstractmethod
    def serialize(self, data: dict, output_path: str) -> None
    @abstractmethod
    def deserialize(self, input_path: str) -> dict
```

#### serializers/serializer_json.py

**Ответственность:**
- JSON сериализация
- JSON.gz сериализация
- Поддержка minify режима

**Публичный API:**
```python
class JSONSerializer(BaseSerializer):
    def __init__(self, minify: bool = False, compress: bool = False)
    def serialize(self, data: dict, output_path: str) -> None
    def deserialize(self, input_path: str) -> dict
```

**Зависимости:**
- `json` (stdlib)
- `gzip` (stdlib)
- `serializer_base.py`
- `utils_logger.py`

#### serializers/serializer_msgpack.py

**Ответственность:**
- MessagePack сериализация
- Бинарный компактный формат

**Публичный API:**
```python
class MessagePackSerializer(BaseSerializer):
    def serialize(self, data: dict, output_path: str) -> None
    def deserialize(self, input_path: str) -> dict
```

**Зависимости:**
- `msgpack` (external)
- `serializer_base.py`
- `utils_logger.py`

---

### 6. viewers/ - Отображение индексов

#### viewers/viewer_index.py

**Ответственность:**
- Человекочитаемый вывод TECH-INDEX
- Фильтрация по типам (functions, classes, modules)
- Форматирование для консоли
- Статистика индекса

**Публичный API:**
```python
class IndexViewer:
    def __init__(self, logger: Logger)
    def view(self, index_path: str, filter_type: str | None = None) -> None
    def show_statistics(self, index: dict) -> None
    def format_function(self, func: list) -> str
    def format_class(self, cls: list) -> str
```

**Зависимости:**
- `serializer_json.py`
- `utils_logger.py`

---

### 7. utils/ - Утилиты

#### utils/utils_logger.py

**Ответственность:**
- Настройка логирования в main.log
- Уровень DEBUG по умолчанию
- Дублирование в консоль
- Форматирование логов

**Публичный API:**
```python
def setup_logger(name: str) -> Logger
def get_logger(name: str) -> Logger
```

**Зависимости:**
- `logging` (stdlib)
- `sys` (stdlib)

#### utils/utils_file.py

**Ответственность:**
- Чтение Python файлов
- Fallback кодировок (UTF-8, CP1251, Latin-1)
- Создание директорий
- Проверка существования файлов

**Публичный API:**
```python
def read_python_file(file_path: str) -> str
def ensure_directory(path: str) -> None
def get_file_hash(file_path: str) -> str
def get_file_modified(file_path: str) -> str
```

**Зависимости:**
- `pathlib` (stdlib)
- `hashlib` (stdlib)
- `datetime` (stdlib)
- `utils_logger.py`

#### utils/utils_hash.py

**Ответственность:**
- Хеширование объектов (классы, функции)
- Поддержка разных длин хешей (8, 16, 32, 64)
- SHA256 алгоритм

**Публичный API:**
```python
def hash_object(content: str, length: int = 16) -> str
def hash_file(file_path: str, length: int = 16) -> str
```

**Зависимости:**
- `hashlib` (stdlib)
- `utils_logger.py`

---

### 8. cli/ - CLI интерфейс

#### cli/cli_index.py

**Ответственность:**
- CLI для генерации TECH-INDEX
- Парсинг аргументов командной строки
- Вызов валидатора
- Оркестрация процесса индексации

**Публичный API:**
```python
class IndexCLI:
    def __init__(self)
    def run(self, args: list[str]) -> None
    def parse_arguments(self, args: list[str]) -> argparse.Namespace
```

**Зависимости:**
- `argparse` (stdlib)
- `validator.py`
- `parser.py`
- `indexer.py`
- `builder_tech_index.py`
- `serializer_*.py`
- `utils_logger.py`

#### cli/cli_location.py

**Ответственность:**
- CLI для генерации TECH-LOCATION
- Парсинг аргументов командной строки
- Вызов валидатора
- Оркестрация процесса построения location

**Публичный API:**
```python
class LocationCLI:
    def __init__(self)
    def run(self, args: list[str]) -> None
    def parse_arguments(self, args: list[str]) -> argparse.Namespace
```

**Зависимости:**
- `argparse` (stdlib)
- `validator.py`
- `builder_location.py`
- `serializer_*.py`
- `utils_logger.py`

---

### 9. main.py - Entry Point

**Ответственность:**
- Главная точка входа
- Маршрутизация команд (index / location / view)
- Обработка глобальных исключений

**Публичный API:**
```python
def main() -> None
```

**Зависимости:**
- `sys` (stdlib)
- `cli_index.py`
- `cli_location.py`
- `viewer_index.py`
- `utils_logger.py`

---

## Поток данных

### Генерация TECH-INDEX

```
1. CLI получает аргументы
   ↓
2. Validator проверяет входные данные
   ↓
3. Parser читает Python файлы → AST
   ↓
4. Indexer анализирует AST → индексы + правила
   ↓
5. TechIndexBuilder строит компактный индекс
   ↓
6. Serializer сохраняет в файл (JSON/JSON.gz/MessagePack)
```

### Генерация TECH-LOCATION

```
1. CLI получает аргументы + путь к TECH-INDEX
   ↓
2. Validator проверяет входные данные
   ↓
3. Serializer загружает TECH-INDEX
   ↓
4. LocationBuilder разворачивает индексы → читаемый формат
   ↓
5. Serializer сохраняет в файл (JSON/JSON.gz)
```

### Просмотр индекса

```
1. CLI получает путь к индексу
   ↓
2. Serializer загружает индекс
   ↓
3. IndexViewer форматирует и выводит в консоль
```

---

## Принципы разработки

### SOLID

**Single Responsibility Principle**
- Каждый модуль отвечает за одну задачу
- `parser.py` - только парсинг
- `indexer.py` - только индексация
- `serializer_*.py` - только сериализация

**Open/Closed Principle**
- Легко добавить новый сериализатор через `BaseSerializer`
- Легко добавить новые правила анализа в `indexer.py`

**Liskov Substitution Principle**
- Все сериализаторы взаимозаменяемы через базовый класс

**Interface Segregation Principle**
- Минимальные публичные API
- Клиенты зависят только от нужных методов

**Dependency Inversion Principle**
- Зависимости передаются через конструктор (DI)
- Нет создания зависимостей внутри классов

### Dependency Injection

Все классы получают зависимости через конструктор:

```python
class TechIndexBuilder:
    def __init__(self, indexer: CodeIndexer, logger: Logger):
        self.indexer = indexer
        self.logger = logger
```

### Разделение ответственности

- **Парсинг** - `parser.py`
- **Анализ** - `indexer.py`
- **Построение** - `builders/`
- **Сериализация** - `serializers/`
- **Отображение** - `viewers/`
- **Утилиты** - `utils/`
- **Интерфейс** - `cli/`

---

## Обработка ошибок

### Стратегия логирования

1. Все исключения логируются перед обработкой
2. Критические ошибки - `logger.exception()`
3. Предупреждения - `logger.warning()`
4. Информация - `logger.info()`
5. Отладка - `logger.debug()`

### Fallback стратегии

- **Кодировки файлов**: UTF-8 → CP1251 → Latin-1
- **Отсутствие msgpack**: предупреждение + fallback на JSON
- **Невалидный AST**: пропуск файла + логирование

---

## Расширяемость

### Добавление нового сериализатора

1. Создать `serializers/serializer_newformat.py`
2. Наследоваться от `BaseSerializer`
3. Реализовать `serialize()` и `deserialize()`
4. Зарегистрировать в CLI

### Добавление нового правила анализа

1. Добавить метод в `CodeIndexer`
2. Добавить поле в схему JSON
3. Обновить `TechIndexBuilder`
4. Обновить `LocationBuilder`

### Добавление нового типа индекса

1. Создать `builders/builder_newtype.py`
2. Создать `cli/cli_newtype.py`
3. Добавить команду в `main.py`

---

## Тестирование

### Структура тестов

```
tests/
├── test_parser.py           # Тесты AST парсинга
├── test_indexer.py          # Тесты индексации
├── test_validator.py        # Тесты валидации
├── test_builder_tech_index.py   # Тесты построения TECH-INDEX
├── test_builder_location.py     # Тесты построения TECH-LOCATION
├── test_serializer_json.py      # Тесты JSON сериализации
├── test_viewer_index.py         # Тесты отображения
└── test_utils_file.py           # Тесты файловых утилит
```

### Минимальное покрытие

- Каждая публичная функция - минимум 2 теста (success + error)
- Бизнес-логика - обязательное покрытие

---

## Производительность

### Оптимизации

- Использование генераторов для больших проектов
- Ленивая загрузка модулей
- Кэширование хешей файлов
- Параллельный парсинг файлов (опционально)

### Ограничения

- Максимальный размер файла для парсинга: 1 МБ
- Максимальная глубина AST: 100 уровней
- Таймаут парсинга файла: 30 секунд

---

## Безопасность

### Валидация входных данных

- Проверка путей на directory traversal
- Ограничение размера входных файлов
- Валидация форматов

### Логирование конфиденциальной информации

- НЕ логировать содержимое секретов
- НЕ логировать пути к конфиденциальным файлам
- Использовать маскирование для чувствительных данных

---

## Совместимость

### Версии Python

- Минимальная: Python 3.10
- Рекомендуемая: Python 3.11+
- Причина 3.10+: использование `int | str` синтаксиса

### Зависимости

**Обязательные:**
- `ast` (stdlib)
- `json` (stdlib)
- `pathlib` (stdlib)
- `argparse` (stdlib)
- `logging` (stdlib)

**Опциональные:**
- `msgpack` - для MessagePack формата

### Обратная совместимость

- TECH-INDEX v3.0 совместим с v2.1, v2.0 (читать)
- TECH-LOCATION v3.0 совместим с v2.0 (читать)

---

## Конфигурация

### Переменные окружения

- `PY_INDEXER_LOG_LEVEL` - уровень логирования (DEBUG, INFO, WARNING, ERROR)
- `PY_INDEXER_MAX_FILE_SIZE` - максимальный размер файла (в байтах)

### Файл конфигурации

Опционально: `pyproject.toml`

```toml
[tool.py-indexer]
log_level = "DEBUG"
max_file_size = 1048576
default_format = "json"
compress_names = false
hash_length = 16
```

---

## Будущие улучшения

1. Параллельный парсинг файлов
2. Инкрементальная индексация (только измененные файлы)
3. Поддержка Python 2 проектов (опционально)
4. Web-интерфейс для просмотра индексов
5. Интеграция с IDE (VS Code, PyCharm)
6. Экспорт в другие форматы (XML, YAML, CSV)
7. Визуализация графа зависимостей

---

## Дополнительные ресурсы

- **Спецификация v3.0**: `index-extension-spec.md`
- **JSON Schema TECH-INDEX**: `tech-index-v3-schema.json`
- **JSON Schema TECH-LOCATION**: `tech-location-v3-schema.json`
- **Примеры**: `example-index-v3.json`, `example-location-v3.json`
