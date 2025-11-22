# PY-Indexer v3.1 - Architecture

**Separation of Concerns Design for Python Code Indexing**

---

## 🎯 Core Principle

```
ONE responsibility per file
ONE source of truth (location_id)
ZERO duplication of data
```

---

## 📊 Architecture Overview

```
┌─────────────────┐
│  Python Project │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Parser  │ (AST analysis)
    └────┬────┘
         │
    ┌────▼────────────────────────────┐
    │  Indexer (location_id generator)│
    └────┬────────────────────────────┘
         │
    ┌────▼────────────────────────────────────┐
    │         4 Specialized Builders           │
    ├──────────┬──────────┬──────────┬────────┤
    │  INDEX   │ LOCATION │DOCSTRINGS│COMMENTS│
    └──────────┴──────────┴──────────┴────────┘
         │          │          │          │
    ┌────▼──────────▼──────────▼──────────▼────┐
    │           Serializers                     │
    │  (JSON / JSON.gz / MessagePack)           │
    └───────────────────────────────────────────┘
```

---

## 🗂️ File Responsibilities

### **TECH-INDEX** (What?)

**Purpose:** Code structure without coordinates

**Contains:**
- ✅ `names[]` - Unified name dictionary
- ✅ `files[]` - File paths
- ✅ `classes[]` - Class definitions (name, bases, location_id)
- ✅ `functions[]` - Function definitions (name, parent, location_id)
- ✅ `typehints{}` - Type annotations by location_id
- ✅ `decorators{}` - Decorator lists by location_id
- ✅ `imports[]` - Import statements
- ❌ NO line numbers
- ❌ NO docstrings
- ❌ NO comments

**Size:** ~2 MB for 1000-file project

**Use cases:**
- AI/LLM analysis
- Code structure queries
- Dependency graphs
- Type checking

---

### **TECH-LOCATION** (Where?)

**Purpose:** File coordinates mapping

**Contains:**
- ✅ `files[]` - File paths (same as INDEX)
- ✅ `classes[]` - [location_id, file_idx, line_start, line_end]
- ✅ `functions[]` - [location_id, file_idx, line_start, line_end]
- ✅ `modules[]` - [location_id, file_idx, line_start, line_end]
- ✅ `imports[]` - [location_id, file_idx, line_number]
- ❌ NO names, types, or structure

**Size:** ~500 KB for 1000-file project

**Use cases:**
- IDE navigation (Go to Definition)
- Code editors integration
- Line number lookups
- File position queries

---

### **TECH-DOCSTRINGS** (Documentation)

**Purpose:** Documentation strings with coordinates

**Contains:**
- ✅ `docstrings_text[]` - Text dictionary (like names[])
- ✅ `modules[]` - [location_id, [[text_idx, file_idx, line_start, line_end]]]
- ✅ `classes[]` - [location_id, [[text_idx, file_idx, line_start, line_end]]]
- ✅ `functions[]` - [location_id, [[text_idx, file_idx, line_start, line_end]]]
- ❌ NO code structure

**Size:** ~1 MB for 1000-file project

**Use cases:**
- Documentation generation
- API docs extraction
- Help text display
- Code review

---

### **TECH-COMMENTS** (Code Comments)

**Purpose:** Code comments with coordinates

**Contains:**
- ✅ `comments_text[]` - Comment text dictionary
- ✅ `modules[]` - [location_id, [[text_idx, file_idx, line_number]]]
- ✅ `classes[]` - [location_id, [[text_idx, file_idx, line_number]]]
- ✅ `functions[]` - [location_id, [[text_idx, file_idx, line_number]]]
- ❌ NO code structure

**Size:** ~300 KB for 1000-file project

**Use cases:**
- TODO/FIXME tracking
- Code review annotations
- Developer notes extraction
- Comment analysis

---

## 🔗 Data Linking

### **location_id as Universal Key**

```python
# All files share location_id as primary key

# INDEX: Structure
classes[0] = [name_idx, bases[], file_idx, location_id=42]

# LOCATION: Coordinates
classes[0] = [location_id=42, file_idx, line_start, line_end]

# DOCSTRINGS: Documentation
classes[0] = [location_id=42, [[text_idx, file_idx, lines]]]

# COMMENTS: Annotations
classes[0] = [location_id=42, [[text_idx, file_idx, line]]]

# location_id=42 links everything together
```

---

## 🏗️ Component Design

### **1. Parser (parser.py)**

**Responsibility:** AST parsing

```python
class ASTParser:
    def parse_file(file) -> ParsedFile:
        # Parse Python to AST
        # Extract classes, functions, imports
        # Extract type hints, decorators
        # Extract docstrings, comments
        return ParsedFile(...)
```

**Output:** Structured Python objects (dataclasses)

---

### **2. Indexer (indexer.py)**

**Responsibility:** location_id generation + name deduplication

```python
class Indexer:
    def __init__(self):
        self.names = NameRegistry()  # Deduplicate names
        self.location_counter = 0
    
    def index_project(path) -> IndexData:
        # Assign unique location_id to each entity
        # Build name dictionary
        # Create file registry
        return IndexData(...)
```

**Key feature:** Assigns globally unique `location_id` to every code entity

---

### **3. Builders (builders/)**

**Responsibility:** Generate specialized JSON structures

```python
# builder_tech_index.py
class TechIndexBuilder:
    def build(index_data) -> dict:
        # Build INDEX structure
        # NO coordinates!
        return {"names": [...], "classes": [...]}

# builder_location.py
class LocationBuilder:
    def build(index_data) -> dict:
        # Build LOCATION structure
        # ONLY coordinates!
        return {"classes": [[id, file, start, end]]}

# builder_docstrings.py
class DocstringsBuilder:
    def build(index_data) -> dict:
        # Build DOCSTRINGS structure
        return {"docstrings_text": [...], "classes": [...]}

# builder_comments.py
class CommentsBuilder:
    def build(index_data) -> dict:
        # Build COMMENTS structure
        return {"comments_text": [...], "classes": [...]}
```

---

### **4. Serializers (serializers/)**

**Responsibility:** Format conversion

```python
class JSONSerializer:
    def serialize(data, path):
        # Write to JSON
        # Optional: minify, compress

class MessagePackSerializer:
    def serialize(data, path):
        # Write to MessagePack (binary)
```

**Formats:**
- JSON - Human-readable
- JSON.gz - Compressed
- MessagePack - Binary, fastest

---

## 📐 Data Flow

```
Source Code (.py files)
    ↓
Parser (AST analysis)
    ↓
ParsedFile objects
    ↓
Indexer (location_id assignment)
    ↓
IndexData (unified structure)
    ↓
┌───────┴──────────────────────────┐
│                                   │
TechIndexBuilder         LocationBuilder
    ↓                                ↓
tech-index.json          tech-location.json
    │                                │
DocstringsBuilder         CommentsBuilder
    ↓                                ↓
tech-docstrings.json     tech-comments.json
```

---

## 🎯 Design Decisions

### **Why Separate Files?**

1. **Modularity** - Load only what you need
2. **Performance** - INDEX is tiny for AI analysis
3. **Flexibility** - Add new indexes without breaking existing
4. **Clarity** - Each file has single responsibility

### **Why location_id?**

1. **Stability** - Line numbers change, location_id doesn't
2. **Linking** - Single key connects all files
3. **Efficiency** - Integer lookups are fast
4. **Versioning** - Track entity changes across commits

### **Why Text Dictionaries?**

```python
# Without dictionary (duplicate text)
{
  "classes": [
    ["AppConfig", "Class for app configuration"],
    ["UserConfig", "Class for user configuration"],
    ["DBConfig", "Class for database configuration"]
  ]
}
# ~300 bytes

# With dictionary (no duplication)
{
  "text": ["AppConfig", "UserConfig", "DBConfig", 
           "Class for app configuration", 
           "Class for user configuration",
           "Class for database configuration"],
  "classes": [[0, 3], [1, 4], [2, 5]]
}
# ~200 bytes (33% smaller)
```

---

## 🔬 Advanced Features

### **Name Registry**

Deduplicates all names across project:

```python
names = NameRegistry()
names.add("AppConfig")  # Returns 0
names.add("int")        # Returns 1
names.add("AppConfig")  # Returns 0 (deduplicated!)
```

### **Type Hints Compression**

```python
# Full type: Optional[Dict[str, List[int]]]
# Stored as: [names_idx array]
typehints = {
  "42": {
    "params": [[3, 15]],  # param_name_idx, type_idx
    "return": 20          # return_type_idx
  }
}
```

### **Multi-level Comments**

```python
# Module-level comment
class User:  # Class-level comment
    def login(self):  # Function-level comment
        pass

# Stored separately with location_id linking
```

---

## 📊 Performance

### **Compression Ratio**

| Project Size | Source | INDEX | LOCATION | DOCSTRINGS | COMMENTS | Total | Ratio |
|--------------|--------|-------|----------|------------|----------|-------|-------|
| Small (100 files) | 50 MB | 200 KB | 50 KB | 100 KB | 30 KB | 380 KB | 130x |
| Medium (1000 files) | 500 MB | 2 MB | 500 KB | 1 MB | 300 KB | 3.8 MB | 130x |
| Large (5000 files) | 5 GB | 10 MB | 2.5 MB | 5 MB | 1.5 MB | 19 MB | 260x |

### **Parse Speed**

- ~100-200 files/second
- ~1 million lines/minute
- Parallel processing support (future)

---

## 🚀 Future Enhancements

### **v3.2 Roadmap**

- [ ] Incremental indexing (only changed files)
- [ ] Parallel processing (multicore)
- [ ] Call graph generation
- [ ] Dependency analysis
- [ ] Security vulnerability detection
- [ ] Code metrics (complexity, duplication)

### **v4.0 Vision**

- [ ] Multi-language support (JS, TS, Go, Rust)
- [ ] Real-time indexing (file watcher)
- [ ] LSP integration (Language Server Protocol)
- [ ] Web UI for visualization
- [ ] Git integration (history tracking)

---

## 📚 References

- **JSON Schema:** http://json-schema.org/
- **AST Documentation:** https://docs.python.org/3/library/ast.html
- **PEP 484 (Type Hints):** https://peps.python.org/pep-0484/

---

**PY-Indexer v3.1** - Clean Architecture. Single Responsibility. AI-Ready.
