# v3.1 Examples (Ultra-Compact)

## TECH-INDEX
```json
{
  "meta": {"version": "3.1", "project": "app"},
  "names": ["AppConfig", "Settings", "load_config", "user_id", "int"],
  "files": ["config.py", "settings.py"],
  "classes": [
    [0, [], 1, 42]
  ],
  "functions": [
    [2, 0, 1, 15]
  ],
  "typehints": {
    "15": {
      "params": [[3, 4]],
      "return": 4
    }
  }
}
```
**Read:** Class "AppConfig"[0] in "settings.py"[1], location_id=42

---

## TECH-LOCATION
```json
{
  "meta": {"version": "3.1", "project": "app"},
  "files": ["config.py", "settings.py"],
  "classes": [
    [42, 1, 23, 56]
  ],
  "functions": [
    [15, 1, 34, 45]
  ]
}
```
**Read:** location_id=42 → settings.py[1] lines 23-56

---

## TECH-DOCSTRINGS
```json
{
  "meta": {"version": "3.1", "project": "app"},
  "docstrings_text": [
    "Configuration module",
    "Settings class"
  ],
  "classes": [
    [42, [[1, 1, 24, 25]]]
  ]
}
```
**Read:** location_id=42 has docstring[1] at settings.py[1]:24-25

---

## TECH-COMMENTS
```json
{
  "meta": {"version": "3.1", "project": "app"},
  "comments_text": [
    "FIXME: Add validation",
    "TODO: Cache results"
  ],
  "functions": [
    [15, [[0, 1, 35]]]
  ]
}
```
**Read:** location_id=15 has comment[0] at settings.py[1]:35

---

## Usage
```python
# Find class AppConfig
class_idx = 0
class_data = index["classes"][0]  # [0, [], 1, 42]
location_id = class_data[3]  # 42

# Get coordinates
loc = location["classes"][0]  # [42, 1, 23, 56]
file = location["files"][loc[1]]  # "settings.py"
lines = f"{loc[2]}-{loc[3]}"  # "23-56"

# Get docstring
doc_data = docstrings["classes"][0]  # [42, [[1, 1, 24, 25]]]
text = docstrings["docstrings_text"][1]  # "Settings class"

# Result: AppConfig in settings.py:23-56 with docstring at :24-25
```
