# PY-Indexer v3.0

Генератор компактных индексов Python проектов для AI-анализа.

Создает два типа индексов:
- **TECH-INDEX** - максимально компактный формат с числовыми ссылками
- **TECH-LOCATION** - человекочитаемый формат с полными именами

## Особенности v3.0

- ✅ Сжатие через индексы (справочники names, files, defaults)
- ✅ Нормализация данных (single source of truth)
- ✅ Массивы вместо объектов для компактности
- ✅ Расширения для проверки правил кодирования:
  - Type hints функций и параметров
  - Default values с проверкой mutable defaults
  - SQL-запросы с флагами безопасности
  - Hardcoded secrets detection
  - Logging usage tracking
  - Global variables detection
  - Class dependencies analysis
  - Docstring formats validation
  - Test coverage tracking

## Требования

- Python 3.10+
- msgpack (опционально, для MessagePack формата)

## Установка

```bash
pip install -r requirements.txt
```

## Быстрый старт

### Генерация TECH-INDEX

```bash
python main.py index /path/to/project /path/to/output
```

### Генерация TECH-LOCATION

```bash
python main.py location /path/to/project /path/to/output /path/to/tech-index.json
```

### Просмотр индекса (человекочитаемый формат)

```bash
python main.py view /path/to/tech-index.json
```

## Опции

### Форматы вывода

- `--format=json` - JSON (по умолчанию)
- `--format=json.gz` - сжатый JSON с GZIP
- `--format=msgpack` - MessagePack (требует msgpack)

### Дополнительные опции

- `--minify` - компактный JSON без отступов
- `--compress-names` - сжатие массива names с GZIP+Base64
- `--hash-len=16` - длина хешей (8, 16, 32, 64)

## Примеры использования

### Генерация сжатого индекса

```bash
python main.py index ./my_project ./output --format=json.gz --minify
```

### Генерация с MessagePack

```bash
python main.py index ./my_project ./output --format=msgpack
```

### Просмотр индекса с фильтрацией

```bash
python main.py view ./output/tech-index.json --filter-type=functions
```

## Структура проекта

```
src/
├── tests/          # Тесты
├── builders/       # Построители индексов
├── serializers/    # Сериализаторы (JSON, MessagePack)
├── viewers/        # Просмотр индексов
├── utils/          # Утилиты (логирование, файлы, хеширование)
├── cli/            # CLI интерфейсы
├── parser.py       # AST парсер
├── indexer.py      # Индексатор
├── validator.py    # Валидация данных
└── main.py         # Entry point
```

## Логирование

Все логи записываются в `main.log` с уровнем DEBUG.

Формат лога:
```
2025-11-22 15:30:45 - module_name - INFO - Message
```

## Схемы данных

Индексы соответствуют JSON Schema v3.0:
- `tech-index-v3-schema.json` - схема для TECH-INDEX
- `tech-location-v3-schema.json` - схема для TECH-LOCATION

## Примеры выходных данных

### TECH-INDEX (компактный)

```json
{
  "meta": {
    "version": "3.0",
    "generated": "2025-11-22T14:30:00Z",
    "project": "example-backend"
  },
  "names": ["UserService", "get_user", "create_user", "user_id", "int"],
  "files": ["app/services/user_service.py"],
  "modules": [[0, 0, -1]],
  "classes": [[0, 14, 0, [], [], -1, []]],
  "functions": [[1, 25, 0], [2, 50, 0]],
  "typehints": [[1, [3, 4], 6]],
  "mutabledefaults": [[2, 0, 50, 10, 11]]
}
```

### TECH-LOCATION (развернутый)

```json
{
  "meta": {
    "version": "3.0",
    "generated": "2025-11-22T14:30:00Z",
    "project": "example-backend"
  },
  "paths": ["app/services/user_service.py"],
  "functions": [
    ["get_user", -1, 0, 25, 38, 25, 26],
    ["create_user", -1, 0, 50, 75, 50, 51]
  ],
  "typehints": [
    ["get_user", ["user_id", "int"], "Optional[User]"],
    ["create_user", ["name", "str", "email", "str"], "User"]
  ],
  "mutabledefaults": [
    ["create_user", "app/services/user_service.py", 50, "tags", "[]", "list"]
  ]
}
```

## Правила проверки кода

PY-Indexer автоматически проверяет:

- ✅ Mutable default arguments (`def func(x=[])`)
- ✅ SQL-инъекции (f-strings в SQL запросах)
- ✅ Hardcoded secrets (API keys, passwords)
- ✅ Глобальные переменные (не константы)
- ✅ Отсутствие логирования в критичных функциях
- ✅ Отсутствие type hints на публичных функциях
- ✅ Отсутствие docstrings
- ✅ Отсутствие тестов для бизнес-логики

## Лицензия

Proprietary. Все права защищены.

## Автор

Разработка: 2025

## Поддержка

При возникновении проблем проверьте файл `main.log` для диагностики.
