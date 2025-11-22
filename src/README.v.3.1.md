# PY-Indexer v3.1

**Compact Python Project Indexer for AI Analysis**

Generates ultra-compact structured indexes of Python codebases with **separation of concerns architecture**.

---

## 🎯 What It Does

Converts **5 GB** of Python code → **~4 MB** of structured JSON indexes:

```
your_project/        TECH-INDEX       (Structure: What?)
├── 1000+ files  →  tech-index.json         ~2 MB
├── Classes          TECH-LOCATION    (Coordinates: Where?)
├── Functions   →   tech-location.json      ~500 KB
├── Imports          TECH-DOCSTRINGS  (Documentation)
└── Types       →   tech-docstrings.json    ~1 MB
                     TECH-COMMENTS    (Code Comments)
                →   tech-comments.json       ~300 KB
```

---

## 🚀 Quick Start

### Installation
```bash
# Clone repository
git clone https://github.com/your/py-indexer.git
cd py-indexer

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage
```bash
# Generate all indexes
python main.py index ./your_project ./output

# Generates:
# - tech-index.json (structure)
# - tech-location.json (coordinates)
# - tech-docstrings.json (documentation)
# - tech-comments.json (comments)
```

---

## 📊 Architecture v3.1

### **Separation of Concerns**

| File | Responsibility | Size | Use Case |
|------|---------------|------|----------|
| **TECH-INDEX** | Code structure (classes, functions, types) | ~2 MB | AI/LLM analysis |
| **TECH-LOCATION** | File coordinates (line numbers) | ~500 KB | Navigation, IDE integration |
| **TECH-DOCSTRINGS** | Documentation strings | ~1 MB | Documentation generation |
| **TECH-COMMENTS** | Code comments | ~300 KB | Code review, TODOs |

### **Key Innovation: location_id**

All files linked by `location_id` - single source of truth:

```python
# INDEX: What is it?
classes[0] = [0, [], 1, 42]  # name_idx, bases, file_idx, location_id

# LOCATION: Where is it?
classes[0] = [42, 1, 23, 56]  # location_id, file_idx, line_start, line_end

# DOCSTRINGS: What's documented?
classes[0] = [42, [[1, 1, 24, 25]]]  # location_id, [[text_idx, file, lines]]

# Linked by location_id = 42
```

---

## 📝 Examples

### Generate Indexes
```bash
# Full project indexing
python main.py index ./backend ./output

# Custom options
python main.py index ./backend ./output --format=json.gz --hash-len=32
```

### View Results
```bash
# View structure
python main.py view ./output/tech-index.json

# Filter by type
python main.py view ./output/tech-index.json --filter=classes
```

---

## 🔧 Features

✅ **Compact Format** - 500x compression (5 GB → 4 MB)  
✅ **Separation of Concerns** - Structure/Location/Docs/Comments split  
✅ **Type Hints** - Full parameter and return type support  
✅ **Decorators** - Tracks all decorators  
✅ **Multiple Formats** - JSON, GZIP, MessagePack  
✅ **Security Analysis** - Detects SQL injections, hardcoded secrets  
✅ **Python 3.10+** - Modern Python support  

---

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed architecture v3.1
- **[EXAMPLES-v3.1.md](EXAMPLES-v3.1.md)** - Usage examples
- **[Schemas](schemas/)** - JSON schemas for all formats

---

## 🎨 Use Cases

### For AI/LLM
```python
# Feed compact TECH-INDEX to ChatGPT
with open("tech-index.json") as f:
    index = json.load(f)
# AI analyzes entire codebase in single context
```

### For IDEs
```python
# Use LOCATION for navigation
def goto_definition(name):
    loc_id = find_in_index(name)
    coords = location["classes"][loc_id]
    open_file(coords[1], coords[2])  # file, line
```

### For Documentation
```python
# Generate docs from DOCSTRINGS
for class_data in docstrings["classes"]:
    loc_id = class_data[0]
    docs = class_data[1]
    generate_docs(loc_id, docs)
```

---

## 🔬 Technical Details

**Supported:**
- Python 3.10, 3.11, 3.12+
- Type hints (Union, Optional, Generics)
- Async/await
- Decorators with arguments
- Multiple inheritance
- Relative imports

**Formats:**
- JSON (human-readable)
- JSON.gz (compressed)
- MessagePack (binary, fastest)

---

## 📦 Output Files

```
output/
├── tech-index.json         # Structure (classes, functions, types)
├── tech-location.json      # Coordinates (file:line mappings)
├── tech-docstrings.json    # Documentation strings
└── tech-comments.json      # Code comments
```

---

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Follow coding standards (see `python-assistant-core.md`)
4. Submit PR

---

## 📄 License

MIT License - See LICENSE file

---

## 🔗 Links

- **GitHub**: https://github.com/your/py-indexer
- **Issues**: https://github.com/your/py-indexer/issues
- **Docs**: https://py-indexer.readthedocs.io

---

**PY-Indexer v3.1** - Compact. Structured. AI-Ready.
