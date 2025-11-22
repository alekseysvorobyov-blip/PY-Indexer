# Спецификация расширения индекса для проверки правил Python Assistant

## Философия и принципы

### Сохранение существующих принципов:

1. **СЖАТИЕ ЧЕРЕЗ ИНДЕКСЫ** - все строки хранятся в справочниках, используются числовые ссылки
2. **НОРМАЛИЗАЦИЯ** - никаких повторений, single source of truth
3. **МАССИВЫ ВМЕСТО ОБЪЕКТОВ** - компактное представление данных
4. **РАЗДЕЛЕНИЕ ИНДЕКСОВ** - tech-index (сжатый) + tech-location (развернутый)

### Новые расширения:

**Добавляем в tech-index (сжатый):**
- `typehints` - type hints функций и параметров
- `defaults` - default values параметров
- `sqlqueries` - SQL-запросы с флагами безопасности
- `hardcodedsecrets` - найденные секреты в коде
- `loggingusage` - использование logger
- `globalvars` - глобальные переменные
- `classdeps` - зависимости классов

**Добавляем в tech-location (развернутый):**
- Развернутые версии тех же данных для удобства чтения

---

## 1. TECH-INDEX расширения

### 1.1. Type Hints

**Структура:** `typehints` - объект с ключами-индексами функций

```json
{
  "typehints": {
    "42": {
      "params": [[3, 0], [5, 1]],
      "return": 2
    }
  }
}
```

**Формат:**
- Ключ: индекс функции из `functions`
- `params`: массив `[name_idx, type_idx]`
  - `name_idx` - индекс имени параметра в `names`
  - `type_idx` - индекс типа в `names` (или -1 если нет)
- `return`: индекс типа возврата в `names` (или -1 если нет)

**Дополнительные справочники:**
```json
{
  "names": [..., "user_id", "int", "Optional[User]", ...]
}
```

**Компактность:** ~15 байт на функцию (вместо ~150 байт в JSON с именами)

---

### 1.2. Default Values

**Структура:** `defaults` - объект с ключами-индексами функций

```json
{
  "defaults": {
    "42": [
      [3, 1, 0],
      [5, 2, -1]
    ]
  }
}
```

**Формат:**
- Ключ: индекс функции
- Значение: массив `[param_name_idx, default_type, default_value_idx]`
  - `param_name_idx` - индекс имени параметра
  - `default_type`: 0=None, 1=list, 2=dict, 3=set, 4=number, 5=string, 6=bool, 7=other
  - `default_value_idx` - индекс в `defaultvalues` или значение (для чисел/bool)

**Дополнительные справочники:**
```json
{
  "defaultvalues": ["0.0", "\"default\"", "[]", "{}", ...]
}
```

**Флаги проблем:**
```json
{
  "defaultissues": [
    [42, 0, 1]
  ]
}
```
- `[func_idx, param_idx, issue_type]`
- `issue_type`: 0=ok, 1=mutable_list, 2=mutable_dict, 3=mutable_set

**Компактность:** ~10 байт на параметр с default

---

### 1.3. SQL Queries

**Структура:** `sqlqueries` - массив запросов

```json
{
  "sqlqueries": [
    [8, 45, 0, 1, 12],
    [8, 67, 1, 0, 13]
  ]
}
```

**Формат:** `[file_idx, line, query_type, is_safe, query_text_idx]`
- `file_idx` - индекс файла
- `line` - номер строки
- `query_type`: 0=SELECT, 1=INSERT, 2=UPDATE, 3=DELETE, 4=OTHER
- `is_safe`: 0=unsafe (f-string/concat), 1=safe (parameterized)
- `query_text_idx` - индекс в `sqlquerytexts`

**Дополнительные справочники:**
```json
{
  "sqlquerytexts": [
    "f\"SELECT * FROM users WHERE id = {user_id}\"",
    "\"SELECT * FROM users WHERE id = ?\""
  ]
}
```

**Компактность:** ~20 байт на запрос

---

### 1.4. Hardcoded Secrets

**Структура:** `hardcodedsecrets` - массив найденных секретов

```json
{
  "hardcodedsecrets": [
    [8, 10, 0, 15],
    [12, 25, 1, 16]
  ]
}
```

**Формат:** `[file_idx, line, pattern_type, var_name_idx]`
- `file_idx` - индекс файла
- `line` - номер строки
- `pattern_type`: 0=API_KEY, 1=PASSWORD, 2=SECRET, 3=TOKEN, 4=PRIVATE_KEY
- `var_name_idx` - индекс имени переменной в `names`

**Компактность:** ~16 байт на секрет

---

### 1.5. Logging Usage

**Структура:** `loggingusage` - объект с метаданными о логировании

```json
{
  "loggingusage": {
    "functions_with_logger": [12, 15, 23, 42],
    "try_except_blocks": [
      [42, 8, 45, 1],
      [43, 8, 67, 0]
    ]
  }
}
```

**Формат `try_except_blocks`:** `[func_idx, file_idx, line, has_logging]`
- `func_idx` - индекс функции
- `file_idx` - индекс файла
- `line` - строка начала try
- `has_logging`: 0=нет логирования, 1=есть logger.error/exception

**Компактность:** ~16 байт на try-except блок

---

### 1.6. Global Variables

**Структура:** `globalvars` - массив глобальных переменных

```json
{
  "globalvars": [
    [8, 10, 42, 0],
    [8, 15, 43, 1]
  ]
}
```

**Формат:** `[file_idx, line, var_name_idx, is_constant]`
- `file_idx` - индекс файла
- `line` - номер строки
- `var_name_idx` - индекс имени переменной
- `is_constant`: 0=переменная (плохо), 1=КОНСТАНТА (ок)

**Компактность:** ~16 байт на переменную

---

### 1.7. Class Dependencies (DI проверка)

**Структура:** `classdeps` - объект с зависимостями классов

```json
{
  "classdeps": {
    "15": {
      "init_params": [[42, 0], [43, 1]],
      "internal_creation": [2, 5]
    }
  }
}
```

**Формат:**
- Ключ: индекс класса из `classes`
- `init_params`: массив `[param_name_idx, type_idx]` - параметры __init__
- `internal_creation`: массив индексов классов, создаваемых внутри (плохо для DI)

**Компактность:** ~20 байт на класс

---

### 1.8. File Sizes

**Структура:** `filesizes` - массив размеров

```json
{
  "filesizes": [1024, 5120, 15360, 20480, ...]
}
```

**Формат:** Массив чисел (размер в байтах), индекс соответствует индексу файла

**Компактность:** ~4-8 байт на файл (число)

---

### 1.9. Docstring Formats

**Структура:** `docstringformats` - объект с метаданными

```json
{
  "docstringformats": {
    "by_function": {
      "42": 0,
      "43": 1,
      "44": 2
    },
    "coverage": {
      "total": 191,
      "with_docstrings": 145,
      "by_format": [80, 30, 15, 20]
    }
  }
}
```

**Формат `by_function`:**
- Ключ: индекс функции
- Значение: 0=NumPy, 1=Google, 2=Sphinx, 3=Unknown, -1=No docstring

**Формат `by_format`:**
- Массив: [NumPy_count, Google_count, Sphinx_count, Unknown_count]

**Компактность:** ~8 байт на функцию

---

### 1.10. Test Coverage

**Структура:** `testcoverage` - связь тестов с функциями

```json
{
  "testcoverage": {
    "42": [120, 121],
    "43": [122]
  }
}
```

**Формат:**
- Ключ: индекс тестируемой функции
- Значение: массив индексов тестовых функций

**Компактность:** ~12 байт на связь

---

## 2. TECH-LOCATION расширения

### 2.1. Type Hints (развернутый)

```json
{
  "typehints": [
    ["create_user", ["name", "str", "email", "str", "age", "int"], "User"],
    ["get_user_by_id", ["user_id", "int"], "Optional[User]"]
  ]
}
```

**Формат:** `[func_name, [param1, type1, param2, type2, ...], return_type]`

---

### 2.2. Mutable Defaults (развернутый)

```json
{
  "mutabledefaults": [
    ["add_item", "app/utils.py", 15, "items", "[]", "list"],
    ["configure", "app/config.py", 28, "options", "{}", "dict"]
  ]
}
```

**Формат:** `[func_name, file_path, line, param_name, default_value, issue_type]`

---

### 2.3. SQL Queries (развернутый)

```json
{
  "sqlqueries": [
    ["app/db/connection.py", 45, "SELECT", false, "f\"SELECT * FROM users WHERE id = {user_id}\""],
    ["app/db/connection.py", 67, "SELECT", true, "\"SELECT * FROM users WHERE id = ?\""]
  ]
}
```

**Формат:** `[file_path, line, query_type, is_safe, query_text]`

---

### 2.4. Hardcoded Secrets (развернутый)

```json
{
  "hardcodedsecrets": [
    ["config.py", 10, "API_KEY", "API_KEY = \"sk_live_12345\""],
    ["app/settings.py", 25, "PASSWORD", "DATABASE_PASSWORD = \"mypassword\""]
  ]
}
```

**Формат:** `[file_path, line, pattern_type, full_line]`

---

### 2.5. Logging Issues (развернутый)

```json
{
  "loggingissues": [
    ["get_user", "app/services/user.py", 45, false, "exception not logged"],
    ["process_payment", "app/services/payment.py", 120, true, "ok"]
  ]
}
```

**Формат:** `[func_name, file_path, line, has_logging, issue_description]`

---

### 2.6. Global Variables (развернутый)

```json
{
  "globalvars": [
    ["DATABASE_CONNECTION", "app/db/connection.py", 10, false, "mutable global"],
    ["MAX_RETRIES", "app/config.py", 15, true, "constant - ok"]
  ]
}
```

**Формат:** `[var_name, file_path, line, is_constant, note]`

---

## 3. Обновленные JSON Schemas

### 3.1. TECH-INDEX-PY-v3.0-schema.json

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TECH-INDEX-PY-v3.0",
  "description": "Максимально компактная схема индексации Python проектов для AI-анализа с расширениями для проверки правил кода",
  "type": "object",
  "required": ["meta", "names", "files"],
  "properties": {
    "meta": {
      "type": "object",
      "properties": {
        "version": {"type": "string"},
        "generated": {"type": "string"},
        "project": {"type": "string"}
      }
    },
    "names": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Справочник всех имен (переменные, функции, классы, типы)"
    },
    "files": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Массив путей к файлам проекта"
    },
    "filesizes": {
      "type": "array",
      "items": {"type": "integer", "minimum": 0},
      "description": "Размеры файлов в байтах (индекс соответствует files)"
    },
    "modules": {
      "type": "array",
      "items": {
        "type": "array",
        "items": [
          {"type": "integer", "minimum": 0, "description": "nameidx"},
          {"type": "integer", "minimum": 0, "description": "fileidx"},
          {"type": "integer", "minimum": -1, "description": "locationid"}
        ]
      }
    },
    "classes": {
      "type": "array",
      "items": {
        "type": "array",
        "minItems": 6
      }
    },
    "functions": {
      "type": "array",
      "items": {"type": "array"}
    },
    "parameters": {
      "type": "object",
      "description": "Параметры функций по ID"
    },
    "docstrings": {
      "type": "array",
      "items": {"type": "array"}
    },
    "imports": {
      "type": "array",
      "items": {"type": "array"}
    },
    "validation": {
      "type": "object"
    },
    
    "typehints": {
      "type": "object",
      "description": "Type hints функций",
      "patternProperties": {
        "^[0-9]+$": {
          "type": "object",
          "properties": {
            "params": {
              "type": "array",
              "items": {
                "type": "array",
                "items": [
                  {"type": "integer", "description": "param_name_idx"},
                  {"type": "integer", "description": "type_idx"}
                ]
              }
            },
            "return": {"type": "integer", "description": "return_type_idx"}
          }
        }
      }
    },
    
    "defaults": {
      "type": "object",
      "description": "Default values параметров",
      "patternProperties": {
        "^[0-9]+$": {
          "type": "array",
          "items": {
            "type": "array",
            "items": [
              {"type": "integer", "description": "param_name_idx"},
              {"type": "integer", "description": "default_type"},
              {"type": "integer", "description": "default_value_idx"}
            ]
          }
        }
      }
    },
    
    "defaultvalues": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Справочник default values"
    },
    
    "defaultissues": {
      "type": "array",
      "items": {
        "type": "array",
        "items": [
          {"type": "integer", "description": "func_idx"},
          {"type": "integer", "description": "param_idx"},
          {"type": "integer", "description": "issue_type"}
        ]
      },
      "description": "Проблемы с mutable defaults"
    },
    
    "sqlqueries": {
      "type": "array",
      "items": {
        "type": "array",
        "items": [
          {"type": "integer", "description": "file_idx"},
          {"type": "integer", "description": "line"},
          {"type": "integer", "description": "query_type"},
          {"type": "integer", "description": "is_safe"},
          {"type": "integer", "description": "query_text_idx"}
        ]
      }
    },
    
    "sqlquerytexts": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Справочник текстов SQL-запросов"
    },
    
    "hardcodedsecrets": {
      "type": "array",
      "items": {
        "type": "array",
        "items": [
          {"type": "integer", "description": "file_idx"},
          {"type": "integer", "description": "line"},
          {"type": "integer", "description": "pattern_type"},
          {"type": "integer", "description": "var_name_idx"}
        ]
      }
    },
    
    "loggingusage": {
      "type": "object",
      "properties": {
        "functions_with_logger": {
          "type": "array",
          "items": {"type": "integer"},
          "description": "Индексы функций использующих logger"
        },
        "try_except_blocks": {
          "type": "array",
          "items": {
            "type": "array",
            "items": [
              {"type": "integer", "description": "func_idx"},
              {"type": "integer", "description": "file_idx"},
              {"type": "integer", "description": "line"},
              {"type": "integer", "description": "has_logging"}
            ]
          }
        }
      }
    },
    
    "globalvars": {
      "type": "array",
      "items": {
        "type": "array",
        "items": [
          {"type": "integer", "description": "file_idx"},
          {"type": "integer", "description": "line"},
          {"type": "integer", "description": "var_name_idx"},
          {"type": "integer", "description": "is_constant"}
        ]
      }
    },
    
    "classdeps": {
      "type": "object",
      "description": "Зависимости классов для проверки DI",
      "patternProperties": {
        "^[0-9]+$": {
          "type": "object",
          "properties": {
            "init_params": {
              "type": "array",
              "items": {
                "type": "array",
                "items": [
                  {"type": "integer", "description": "param_name_idx"},
                  {"type": "integer", "description": "type_idx"}
                ]
              }
            },
            "internal_creation": {
              "type": "array",
              "items": {"type": "integer"},
              "description": "Индексы классов создаваемых внутри"
            }
          }
        }
      }
    },
    
    "docstringformats": {
      "type": "object",
      "properties": {
        "by_function": {
          "type": "object",
          "patternProperties": {
            "^[0-9]+$": {"type": "integer", "minimum": -1, "maximum": 3}
          },
          "description": "0=NumPy, 1=Google, 2=Sphinx, 3=Unknown, -1=None"
        },
        "coverage": {
          "type": "object",
          "properties": {
            "total": {"type": "integer"},
            "with_docstrings": {"type": "integer"},
            "by_format": {
              "type": "array",
              "items": {"type": "integer"},
              "minItems": 4,
              "maxItems": 4,
              "description": "[NumPy, Google, Sphinx, Unknown]"
            }
          }
        }
      }
    },
    
    "testcoverage": {
      "type": "object",
      "description": "Связь тестов с функциями",
      "patternProperties": {
        "^[0-9]+$": {
          "type": "array",
          "items": {"type": "integer"},
          "description": "Массив индексов тестовых функций"
        }
      }
    }
  }
}
```

---

### 3.2. TECH-LOCATION-v3.0-schema.json

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TECH-LOCATION-v3.0",
  "description": "Развернутая схема для физического расположения объектов Python проекта с расширениями для проверки правил",
  "type": "object",
  "required": ["meta", "paths"],
  "properties": {
    "meta": {
      "type": "object"
    },
    "paths": {
      "type": "array",
      "items": {"type": "string"}
    },
    "modifieds": {
      "type": "array",
      "items": {"type": "string"}
    },
    "hashes": {
      "type": "array",
      "items": {"type": "string"}
    },
    "files": {
      "type": "array",
      "items": {"type": "array"}
    },
    "modules": {
      "type": "array",
      "items": {"type": "array"}
    },
    "classes": {
      "type": "array",
      "items": {"type": "array"}
    },
    "functions": {
      "type": "array",
      "items": {"type": "array"}
    },
    "imports": {
      "type": "array",
      "items": {"type": "array"}
    },
    "decorators": {
      "type": "array",
      "items": {"type": "string"}
    },
    "commenttexts": {
      "type": "array",
      "items": {"type": "string"}
    },
    "comments": {
      "type": "array",
      "items": {"type": "array"}
    },
    
    "typehints": {
      "type": "array",
      "items": {
        "type": "array",
        "minItems": 3,
        "items": [
          {"type": "string", "description": "func_name"},
          {"type": "array", "description": "params [name, type, ...]"},
          {"type": "string", "description": "return_type"}
        ]
      }
    },
    
    "mutabledefaults": {
      "type": "array",
      "items": {
        "type": "array",
        "items": [
          {"type": "string", "description": "func_name"},
          {"type": "string", "description": "file_path"},
          {"type": "integer", "description": "line"},
          {"type": "string", "description": "param_name"},
          {"type": "string", "description": "default_value"},
          {"type": "string", "description": "issue_type"}
        ]
      }
    },
    
    "sqlqueries": {
      "type": "array",
      "items": {
        "type": "array",
        "items": [
          {"type": "string", "description": "file_path"},
          {"type": "integer", "description": "line"},
          {"type": "string", "description": "query_type"},
          {"type": "boolean", "description": "is_safe"},
          {"type": "string", "description": "query_text"}
        ]
      }
    },
    
    "hardcodedsecrets": {
      "type": "array",
      "items": {
        "type": "array",
        "items": [
          {"type": "string", "description": "file_path"},
          {"type": "integer", "description": "line"},
          {"type": "string", "description": "pattern_type"},
          {"type": "string", "description": "full_line"}
        ]
      }
    },
    
    "loggingissues": {
      "type": "array",
      "items": {
        "type": "array",
        "items": [
          {"type": "string", "description": "func_name"},
          {"type": "string", "description": "file_path"},
          {"type": "integer", "description": "line"},
          {"type": "boolean", "description": "has_logging"},
          {"type": "string", "description": "issue_description"}
        ]
      }
    },
    
    "globalvars": {
      "type": "array",
      "items": {
        "type": "array",
        "items": [
          {"type": "string", "description": "var_name"},
          {"type": "string", "description": "file_path"},
          {"type": "integer", "description": "line"},
          {"type": "boolean", "description": "is_constant"},
          {"type": "string", "description": "note"}
        ]
      }
    },
    
    "classdependencies": {
      "type": "array",
      "items": {
        "type": "array",
        "items": [
          {"type": "string", "description": "class_name"},
          {"type": "string", "description": "file_path"},
          {"type": "array", "description": "init_params [name, type]"},
          {"type": "array", "description": "internal_creations [class_names]"}
        ]
      }
    },
    
    "docstringformats": {
      "type": "array",
      "items": {
        "type": "array",
        "items": [
          {"type": "string", "description": "func_name"},
          {"type": "string", "description": "file_path"},
          {"type": "string", "description": "format (NumPy/Google/Sphinx/Unknown/None)"}
        ]
      }
    },
    
    "testcoverage": {
      "type": "array",
      "items": {
        "type": "array",
        "items": [
          {"type": "string", "description": "func_name"},
          {"type": "string", "description": "file_path"},
          {"type": "array", "description": "test_functions [names]"},
          {"type": "integer", "description": "test_count"}
        ]
      }
    }
  }
}
```

---

## 4. Контрольный пример

### 4.1. Пример кода для индексации

```python
# app/services/user_service.py
import logging
from typing import Optional
from app.models.database import User
from app.db.connection import Database

logger = logging.getLogger(__name__)

API_KEY = "sk_live_12345"  # Hardcoded secret
MAX_RETRIES = 3  # Константа - ок

db_connection = None  # Глобальная переменная - плохо


class UserService:
    """User service with business logic.
    
    Parameters
    ----------
    database : Database
        Database connection instance
    """
    
    def __init__(self, database: Database):
        self.db = database
        self.logger = logging.getLogger(__name__)
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID.
        
        Parameters
        ----------
        user_id : int
            User identifier
            
        Returns
        -------
        Optional[User]
            User object or None
        """
        try:
            # SQL-инъекция - использует f-string
            query = f"SELECT * FROM users WHERE id = {user_id}"
            result = self.db.execute(query)
            return result
        except Exception as e:
            # Нет логирования - плохо
            return None
    
    def create_user(self, name: str, email: str, tags: list = []) -> User:
        """Create new user.
        
        Parameters
        ----------
        name : str
            User name
        email : str
            User email
        tags : list, optional
            User tags (default: [])  ← Mutable default!
            
        Returns
        -------
        User
            Created user
        """
        logger.info(f"Creating user: {name}")
        
        user = User(name=name, email=email)
        try:
            self.db.save(user)
        except Exception as e:
            logger.exception(f"Failed to save user: {e}")  # Правильно!
            raise
        
        return user


def test_get_user():
    """Test get_user method."""
    service = UserService(Database())
    user = service.get_user(123)
    assert user is not None


def test_get_user_not_found():
    """Test get_user with invalid ID."""
    service = UserService(Database())
    user = service.get_user(999)
    assert user is None
```

---

### 4.2. Сгенерированный TECH-INDEX (сжатый)

```json
{
  "meta": {
    "version": "3.0",
    "generated": "2025-11-22T14:30:00",
    "project": "example-backend"
  },
  "names": [
    "UserService",
    "get_user",
    "create_user",
    "user_id",
    "int",
    "Optional",
    "User",
    "name",
    "str",
    "email",
    "tags",
    "list",
    "Database",
    "database",
    "API_KEY",
    "MAX_RETRIES",
    "db_connection",
    "test_get_user",
    "test_get_user_not_found"
  ],
  "files": [
    "app/services/user_service.py"
  ],
  "filesizes": [
    2048
  ],
  "functions": [
    [1, 25, 0],
    [2, 50, 0],
    [17, 80, 0],
    [18, 88, 0]
  ],
  
  "typehints": {
    "0": {
      "params": [[3, 4]],
      "return": 5
    },
    "1": {
      "params": [[7, 8], [9, 8], [10, 11]],
      "return": 6
    }
  },
  
  "defaults": {
    "1": [
      [10, 1, 0]
    ]
  },
  "defaultvalues": [
    "[]"
  ],
  "defaultissues": [
    [1, 0, 1]
  ],
  
  "sqlqueries": [
    [0, 28, 0, 0, 0]
  ],
  "sqlquerytexts": [
    "f\"SELECT * FROM users WHERE id = {user_id}\""
  ],
  
  "hardcodedsecrets": [
    [0, 9, 0, 14]
  ],
  
  "loggingusage": {
    "functions_with_logger": [1],
    "try_except_blocks": [
      [0, 0, 27, 0],
      [1, 0, 67, 1]
    ]
  },
  
  "globalvars": [
    [0, 9, 14, 0],
    [0, 10, 15, 1],
    [0, 12, 16, 0]
  ],
  
  "classdeps": {
    "0": {
      "init_params": [[13, 12]],
      "internal_creation": []
    }
  },
  
  "docstringformats": {
    "by_function": {
      "0": 0,
      "1": 0,
      "2": -1,
      "3": -1
    },
    "coverage": {
      "total": 4,
      "with_docstrings": 2,
      "by_format": [2, 0, 0, 0]
    }
  },
  
  "testcoverage": {
    "0": [2, 3]
  }
}
```

**Размер:** ~1.5 КБ (вместо ~10 КБ в развернутом виде)

---

### 4.3. Сгенерированный TECH-LOCATION (развернутый)

```json
{
  "meta": {
    "version": "3.0",
    "generated": "2025-11-22T14:30:00"
  },
  "paths": [
    "app/services/user_service.py"
  ],
  
  "typehints": [
    ["get_user", ["user_id", "int"], "Optional[User]"],
    ["create_user", ["name", "str", "email", "str", "tags", "list"], "User"]
  ],
  
  "mutabledefaults": [
    ["create_user", "app/services/user_service.py", 50, "tags", "[]", "list"]
  ],
  
  "sqlqueries": [
    ["app/services/user_service.py", 28, "SELECT", false, "f\"SELECT * FROM users WHERE id = {user_id}\""]
  ],
  
  "hardcodedsecrets": [
    ["app/services/user_service.py", 9, "API_KEY", "API_KEY = \"sk_live_12345\""]
  ],
  
  "loggingissues": [
    ["get_user", "app/services/user_service.py", 27, false, "exception not logged"],
    ["create_user", "app/services/user_service.py", 67, true, "ok"]
  ],
  
  "globalvars": [
    ["API_KEY", "app/services/user_service.py", 9, false, "hardcoded secret"],
    ["MAX_RETRIES", "app/services/user_service.py", 10, true, "constant - ok"],
    ["db_connection", "app/services/user_service.py", 12, false, "mutable global"]
  ],
  
  "classdependencies": [
    ["UserService", "app/services/user_service.py", [["database", "Database"]], []]
  ],
  
  "docstringformats": [
    ["get_user", "app/services/user_service.py", "NumPy"],
    ["create_user", "app/services/user_service.py", "NumPy"],
    ["test_get_user", "app/services/user_service.py", "None"],
    ["test_get_user_not_found", "app/services/user_service.py", "None"]
  ],
  
  "testcoverage": [
    ["get_user", "app/services/user_service.py", ["test_get_user", "test_get_user_not_found"], 2]
  ]
}
```

**Размер:** ~2.5 КБ

---

## 5. Валидация правил на основе индекса

### Проверки которые теперь возможны:

```python
# 1. Type hints на всех публичных функциях
missing_type_hints = [
    func_idx for func_idx in functions
    if func_idx not in typehints and not is_private(func_idx)
]

# 2. Файлы ≤ 20 Кб
oversized_files = [
    (file_idx, size) for file_idx, size in enumerate(filesizes)
    if size > 20480
]

# 3. Нет mutable defaults
mutable_defaults = defaultissues  # Уже готовый список

# 4. Только параметризованные SQL
unsafe_sql = [
    query for query in sqlqueries
    if query[3] == 0  # is_safe == False
]

# 5. Секреты в .env
hardcoded_secrets = hardcodedsecrets  # Готовый список

# 6. Все исключения логируются
unlogged_exceptions = [
    block for block in loggingusage["try_except_blocks"]
    if block[3] == 0  # has_logging == False
]

# 7. Docstrings в правильном формате
missing_docstrings = [
    func_idx for func_idx, format in docstringformats["by_function"].items()
    if format == -1
]

# 8. Нет глобальных переменных
bad_globals = [
    var for var in globalvars
    if var[3] == 0  # is_constant == False
]

# 9. Dependency Injection
bad_di = [
    class_idx for class_idx, deps in classdeps.items()
    if len(deps["internal_creation"]) > 0
]

# 10. Минимум 2 теста
insufficient_tests = [
    func_idx for func_idx, tests in testcoverage.items()
    if len(tests) < 2
]
```

---

## 6. Преимущества расширенного индекса

### Компактность сохранена:

| Данные | Без индекса | С индексом (v3.0) | Экономия |
|--------|-------------|-------------------|----------|
| Type hints (100 функций) | ~15 КБ | ~1.5 КБ | 90% |
| SQL queries (50 запросов) | ~7.5 КБ | ~1 КБ | 87% |
| Secrets (10 находок) | ~1 КБ | ~160 байт | 84% |
| Logging (100 блоков) | ~10 КБ | ~1.6 КБ | 84% |
| **ИТОГО** | ~33.5 КБ | ~4.3 КБ | **87%** |

### Автоматическая проверка:

```python
def validate_project_rules(tech_index):
    """Автоматическая проверка всех правил Python Assistant."""
    
    issues = {
        "type_hints_missing": check_type_hints(tech_index),
        "oversized_files": check_file_sizes(tech_index),
        "mutable_defaults": tech_index["defaultissues"],
        "unsafe_sql": check_sql_safety(tech_index),
        "hardcoded_secrets": tech_index["hardcodedsecrets"],
        "unlogged_exceptions": check_logging(tech_index),
        "missing_docstrings": check_docstrings(tech_index),
        "global_variables": check_globals(tech_index),
        "bad_dependency_injection": check_di(tech_index),
        "insufficient_tests": check_test_coverage(tech_index)
    }
    
    return issues
```

**Результат:** Мгновенная валидация проекта на соответствие всем правилам!

---

## 7. Совместимость

### Обратная совместимость:

- ✅ Все новые поля **опциональны**
- ✅ Старые индексы работают без изменений
- ✅ Постепенная миграция возможна

### Версионирование:

```json
{
  "meta": {
    "version": "3.0",
    "schema_version": "3.0",
    "backward_compatible_with": ["2.1", "2.0"]
  }
}
```

---

## Итого

**Создана полная спецификация расширения индекса:**

✅ Сохранены все принципы компактности  
✅ Добавлены все необходимые проверки правил  
✅ Созданы новые JSON Schemas (v3.0)  
✅ Предоставлен контрольный пример  
✅ Экономия размера индекса: ~87%  
✅ Автоматическая валидация всех 10 правил

**Готово к реализации!**