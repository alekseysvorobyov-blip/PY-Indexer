# TECH-LOCATION Builder v2.0 - Technical Specification (Compact Format)

## 📋 Document Information

**Version:** 2.0 (Compact)  
**Date:** 2025-11-15  
**Status:** PRODUCTION READY  
**Related Projects:** TECH-INDEX-PY v3.0

---

## 🎯 Changes in v2.0

### Main Difference: Compact Array Format

**v1.0 (objects):**
```json
{
  "files": {
    "0": {
      "path": "module.py",
      "line_count": 150,
      "size_bytes": 4567,
      "last_modified": "2025-11-15T14:30:00",
      "hash": "a1b2c3d4"
    }
  }
}
```

**v2.0 (arrays):**
```json
{
  "paths": ["module.py", "package/__init__.py"],
  "modifieds": ["2025-11-15T14:30:00", "2025-11-15T14:25:00"],
  "hashes": ["a1b2c3d4", "b2c3d4e5"],
  "files": [
    [0, 150, 4567, 0, 0]
  ]
}
```

### Benefits of v2.0

1. **Compactness** - 40-60% size reduction
2. **Deduplication** - identical strings stored once
3. **Compatibility** - similar approach as TECH-INDEX
4. **Speed** - faster parsing and less memory
5. **Case-insensitive comment search** - IGNORECASE support
6. **Minified JSON** - optional --minify parameter

---

## 📐 TECH-LOCATION v2.0 Structure

### General JSON Structure

```json
{
  "meta": { /* metadata */ },
  "paths": [ /* file paths */ ],
  "modifieds": [ /* modification dates */ ],
  "hashes": [ /* SHA256 hashes */ ],
  "decorators": [ /* decorator texts */ ],
  "commenttexts": [ /* comment texts */ ],
  "files": [ /* file data */ ],
  "modules": [ /* module coordinates */ ],
  "classes": [ /* class coordinates */ ],
  "functions": [ /* function coordinates */ ],
  "imports": [ /* import coordinates */ ],
  "comments": [ /* important comments */ ]
}
```

---

## 📊 Index Sections

### 1. meta (Metadata)

No changes from v1.0.

```json
{
  "version": "2.0",
  "schemaversion": "2.0",
  "indexeddate": "2025-11-15T15:30:00.000000",
  "techindexhash": "a1b2c3d4e5f6g7h8",
  "projectroot": "D:\\PROJECT",
  "techindexpath": "D:\\INDEXES\\tech-index-py-v3.json",
  "totalobjects": {
    "modules": 30,
    "classes": 19,
    "functions": 158,
    "imports": 245,
    "comments": 87
  }
}
```

---

### 2. paths (File Paths)

**Purpose:** Array of relative file paths

**Format:** String array

```json
[
  "module.py",
  "package/__init__.py",
  "package/submodule.py"
]
```

**Usage:** Indexed from `files[]`

---

### 3. modifieds (Modification Dates)

**Purpose:** Array of file last modification dates

**Format:** ISO-8601 string array

```json
[
  "2025-11-15T14:30:00.000000",
  "2025-11-15T14:25:00.000000",
  "2025-11-15T14:20:00.000000"
]
```

**Usage:** Indexed from `files[]`

---

### 4. hashes (File Hashes)

**Purpose:** Array of SHA256 file hashes

**Format:** String array (shortened hashes)

```json
[
  "a1b2c3d4e5f6g7h8",
  "b2c3d4e5f6g7h8i9",
  "c3d4e5f6g7h8i9j0"
]
```

**Usage:** Indexed from `files[]`

---

### 5. decorators (Decorators)

**Purpose:** Array of decorator texts

**Format:** String array

```json
[
  "@dataclass",
  "@staticmethod",
  "@property",
  "@decorator(...)"
]
```

**Usage:** Indexed from `classes[]` and `functions[]`

---

### 6. commenttexts (Comment Texts)

**Purpose:** Array of important comment texts

**Format:** String array

```json
[
  "Implement caching mechanism",
  "Handle edge case with empty list",
  "Refactor this code"
]
```

**Usage:** Indexed from `comments[]`

**Comment Types:** TODO, FIXME, NOTE, WARNING, HACK, XXX, OPTIMIZE (case-insensitive search with IGNORECASE)

---

### 7. files (File Data)

**Purpose:** Information about all project files

**Format:** Array of arrays `[path_idx, line_count, size_bytes, modified_idx, hash_idx]`

```json
[
  [0, 150, 4567, 0, 0],
  [1, 25, 890, 1, 1],
  [2, 200, 8900, 2, 2]
]
```

**Fields:**
- `[0]` - path index in `paths[]`
- `[1]` - line count in file
- `[2]` - file size in bytes
- `[3]` - modification date index in `modifieds[]`
- `[4]` - hash index in `hashes[]`

**Example:**
```python
file_data = files[0]
path = paths[file_data[0]]  # "module.py"
line_count = file_data[1]    # 150
size = file_data[2]          # 4567
modified = modifieds[file_data[3]]  # "2025-11-15T14:30:00"
hash_val = hashes[file_data[4]]     # "a1b2c3d4e5f6g7h8"
```

---

### 8. modules (Module Coordinates)

**Purpose:** Module location in files

**Format:** Array of arrays `[module_id, location_id, file_id, line_start, line_end, docstring?]`

```json
[
  [0, 1, 0, 1, 150],
  [1, 2, 1, 1, 25, [1, 5]]
]
```

**Fields:**
- `[0]` - module_id (module index in TECH-INDEX)
- `[1]` - location_id (location ID for linking)
- `[2]` - file_id (file index)
- `[3]` - line_start (first line)
- `[4]` - line_end (last line)
- `[5]` - docstring `[line_start, line_end]` (optional)

---

### 9. classes (Class Coordinates)

**Purpose:** Class locations

**Format:** Array of arrays `[class_id, location_id, file_id, line_start, line_end, definition_line, body_start, indentation, decorators?, docstring?]`

```json
[
  [0, 10, 0, 10, 50, 12, 15, 0, [[10, 0], [11, 1]], [13, 14]]
]
```

**Fields:**
- `[0]` - class_id
- `[1]` - location_id
- `[2]` - file_id
- `[3]` - line_start (first line with decorators)
- `[4]` - line_end (last class line)
- `[5]` - definition_line (line with `class ClassName:`)
- `[6]` - body_start (first body line after docstring)
- `[7]` - indentation (indent in spaces)
- `[8]` - decorators `[[line, decorator_idx], ...]` (optional)
- `[9]` - docstring `[line_start, line_end]` (optional)

**Example:**
```python
cls = classes[0]
class_id = cls[0]           # 0
location_id = cls[1]        # 10
file_id = cls[2]            # 0
line_start = cls[3]         # 10
line_end = cls[4]           # 50
definition_line = cls[5]    # 12
body_start = cls[6]         # 15
indentation = cls[7]        # 0

if len(cls) > 8:
    decorators = cls[8]     # [[10, 0], [11, 1]]
    for dec in decorators:
        line = dec[0]       # 10
        dec_text = decorators_array[dec[1]]  # "@dataclass"

if len(cls) > 9:
    docstring = cls[9]      # [13, 14]
```

---

### 10. functions (Function Coordinates)

**Purpose:** Function and method locations

**Format:** Array of arrays `[function_id, location_id, file_id, line_start, line_end, signature_line, body_start, indentation, decorators?, docstring?]`

```json
[
  [0, 20, 0, 20, 35, 21, 25, 4, [[20, 2]], [22, 24]]
]
```

**Fields:** Similar to classes
- `[0]` - function_id
- `[1]` - location_id
- `[2]` - file_id
- `[3]` - line_start
- `[4]` - line_end
- `[5]` - signature_line (line with `def function_name(...):`)
- `[6]` - body_start
- `[7]` - indentation
- `[8]` - decorators `[[line, decorator_idx], ...]` (optional)
- `[9]` - docstring `[line_start, line_end]` (optional)

---

### 11. imports (Import Coordinates)

**Purpose:** Import statement locations

**Format:** Array of arrays `[import_id, file_id, line, type]`

```json
[
  [0, 0, 1, 0],
  [1, 0, 2, 1],
  [2, 0, 3, 1]
]
```

**Fields:**
- `[0]` - import_id (sequential number)
- `[1]` - file_id (file index)
- `[2]` - line (line number)
- `[3]` - type (0 = `import`, 1 = `from...import`)

---

### 12. comments (Important Comments)

**Purpose:** TODO, FIXME, etc. comments

**Format:** Array of arrays `[file_id, line, type_idx, content_idx]`

```json
[
  [0, 45, 0, 0],
  [1, 23, 1, 1]
]
```

**Fields:**
- `[0]` - file_id (file index)
- `[1]` - line (line number)
- `[2]` - type_idx (0=TODO, 1=FIXME, 2=NOTE, 3=WARNING, 4=HACK, 5=XXX, 6=OPTIMIZE)
- `[3]` - content_idx (text index in `commenttexts[]`)

**Example:**
```python
comment = comments[0]
file_id = comment[0]         # 0
line = comment[1]            # 45
type_idx = comment[2]        # 0 (TODO)
content = commenttexts[comment[3]]  # "Implement caching mechanism"
```

**Note:** Comment search is **case-insensitive** (IGNORECASE) - finds TODO, todo, Todo, etc.

---

## 🔧 Usage

### Basic Usage

```bash
python location_index_builder_v2.py <project_path> <tech_index_dir> <output_dir>
```

### Parameters

- `project_path` - path to Python project
- `tech_index_dir` - directory with TECH-INDEX
- `output_dir` - directory to save TECH-LOCATION
- `--format` - format: `json`, `json.gz` (default: `json`)
- `--minify` - minified JSON (no indentation)

### Examples

```bash
# Basic run (formatted JSON)
python location_index_builder_v2.py "D:\INDEX_GENERATOR\v2" "D:\AI-CodeGuard\TECH-INDEX-PY\Idx" "D:\AI-CodeGuard\TECH-INDEX-PY\Idx"

# Minified JSON
python location_index_builder_v2.py "D:\INDEX_GENERATOR\v2" "D:\AI-CodeGuard\TECH-INDEX-PY\Idx" "D:\AI-CodeGuard\TECH-INDEX-PY\Idx" --minify

# GZIP compression
python location_index_builder_v2.py "D:\INDEX_GENERATOR\v2" "D:\AI-CodeGuard\TECH-INDEX-PY\Idx" "D:\AI-CodeGuard\TECH-INDEX-PY\Idx" --format=json.gz
```

---

## 📊 File Sizes

### Comparison v1.0 vs v2.0

| Metric | v1.0 (objects) | v2.0 (arrays) | Savings |
|---------|----------------|----------------|----------|
| JSON size | 100% | ~50% | ~50% |
| JSON.GZ size | 100% | ~40% | ~60% |
| JSON minified | N/A | ~65% | ~35% |
| Parsing | Baseline | Faster | +30% |
| Memory | Baseline | Less | -40% |

### Typical Sizes (v2.0)

| Project | Files | JSON | JSON (minified) | JSON.GZ |
|--------|-------|------|-----------------|---------|
| Small (10 files) | ~1000 lines | ~50 KB | ~32 KB | ~10 KB |
| Medium (50 files) | ~5000 lines | ~250 KB | ~160 KB | ~50 KB |
| Large (200 files) | ~20000 lines | ~1 MB | ~640 KB | ~200 KB |

---

## 🎓 Data Usage Examples

### Example 1: Get File Information

```python
import json

with open('tech-location-v2.json') as f:
    location = json.load(f)

# File 0
file_data = location['files'][0]
path = location['paths'][file_data[0]]
line_count = file_data[1]
size_bytes = file_data[2]
modified = location['modifieds'][file_data[3]]
file_hash = location['hashes'][file_data[4]]

print(f"File: {path}")
print(f"Lines: {line_count}")
print(f"Size: {size_bytes} bytes")
print(f"Modified: {modified}")
print(f"Hash: {file_hash}")
```

### Example 2: Find Class and Coordinates

```python
# Find class 0
cls = location['classes'][0]
class_id = cls[0]
location_id = cls[1]
file_id = cls[2]
line_start = cls[3]
line_end = cls[4]

file_path = location['paths'][location['files'][file_id][0]]

print(f"Class ID: {class_id}")
print(f"File: {file_path}")
print(f"Lines: {line_start}-{line_end}")

# Decorators
if len(cls) > 8 and cls[8]:
    print("Decorators:")
    for dec in cls[8]:
        line = dec[0]
        dec_text = location['decorators'][dec[1]]
        print(f"  Line {line}: {dec_text}")

# Docstring
if len(cls) > 9 and cls[9]:
    doc_start, doc_end = cls[9]
    print(f"Docstring: lines {doc_start}-{doc_end}")
```

### Example 3: Get All TODO Comments

```python
for comment in location['comments']:
    file_id = comment[0]
    line = comment[1]
    type_idx = comment[2]
    content_idx = comment[3]
    
    if type_idx == 0:  # TODO
        file_path = location['paths'][location['files'][file_id][0]]
        content = location['commenttexts'][content_idx]
        print(f"{file_path}:{line} - TODO: {content}")
```

---

## 📏 Size Optimization

### Applied Techniques

1. **Arrays instead of objects** - 40% savings
2. **String indexing** - deduplication of paths, dates, hashes
3. **Compact coordinates** - minimal arrays
4. **Optional fields** - not added if empty
5. **Numeric types** - instead of strings where possible
6. **Minified JSON** - optional --minify parameter

### TECH-INDEX + TECH-LOCATION Size

| Format | TECH-INDEX | TECH-LOCATION | Total |
|--------|------------|---------------|-------|
| JSON formatted | ~1 MB | ~250 KB | ~1.25 MB |
| JSON minified | ~640 KB | ~160 KB | ~800 KB |
| JSON.GZ | ~200 KB | ~40 KB | ~240 KB |

---

## 🔍 TECH-INDEX Integration

### Linking via location_id

```python
# Find class in TECH-INDEX
tech_index = json.load(open('tech-index-py-v3.json'))
class_data = tech_index['classes'][5]
location_id = class_data[5]  # get location_id

# Find coordinates in TECH-LOCATION
location = json.load(open('tech-location-v2.json'))
for cls in location['classes']:
    if cls[1] == location_id:  # cls[1] = location_id
        print(f"Class found:")
        print(f"  Lines: {cls[3]}-{cls[4]}")
        break
```

---

## 📝 Differences from v1.0

### Structural Changes

| Section | v1.0 | v2.0 |
|--------|------|------|
| files | Object with fields | Array of arrays + indexes |
| modules | Objects | Arrays |
| classes | Objects | Arrays |
| functions | Objects | Arrays |
| imports | Objects | Arrays |
| comments | Objects | Arrays |

### New Sections in v2.0

- `paths[]` - file path array
- `modifieds[]` - modification date array
- `hashes[]` - hash array
- `decorators[]` - decorator text array
- `commenttexts[]` - comment text array

### New Features in v2.0

- **IGNORECASE** - case-insensitive comment search (TODO, todo, Todo)
- **--minify** - minified JSON output option
- Improved performance and memory usage

---

## ⚠️ Backward Compatibility

**v2.0 is NOT compatible with v1.0** due to format changes.

Projects using v1.0 must be updated for v2.0.

---

## 🚀 Key Features

**TECH-LOCATION Builder v2.0** provides:

✅ Compact array format (40-60% size reduction)  
✅ String deduplication (paths, dates, hashes, decorators, comments)  
✅ Case-insensitive comment search (IGNORECASE)  
✅ Formatted JSON output (default)  
✅ Minified JSON output (--minify, -35% size)  
✅ GZIP compression (--format=json.gz, -84% size)  
✅ Automatic TECH-INDEX search  
✅ Synchronization check (techindexhash)  
✅ Full TECH-INDEX v3.0 compatibility

---

## 📄 License

**Creation Date:** 2025-11-15  
**Document Version:** 2.0.0  
**Status:** PRODUCTION READY

---

**End of Document**
