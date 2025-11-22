# Базовый (хеши 16 символов, names не сжаты)
python tech_gen_v21.py "D:\INDEX_GENERATOR\v2" "D:\AI-CodeGuard\TECH-INDEX-PY"

# С сжатием names
python tech_gen_v21.py "D:\INDEX_GENERATOR\v2" "D:\AI-CodeGuard\TECH-INDEX-PY" --compress-names

# Длинные хеши (32 символа)
python tech_gen_v21.py "D:\INDEX_GENERATOR\v2" "D:\AI-CodeGuard\TECH-INDEX-PY" --hash-len=32

# Максимальная компактность
python tech_gen_v21.py "D:\INDEX_GENERATOR\v2" "D:\AI-CodeGuard\TECH-INDEX-PY" --compress-names --hash-len=16

# РЕКОМЕНДУЕТСЯ: GZIP (95% экономии)
python tech_index_generator_v22.py "D:\INDEX_GENERATOR\v2" "D:\AI-CodeGuard\TECH-INDEX-PY" --format=json.gz

# Обычный minified JSON
python tech_index_generator_v22.py "D:\INDEX_GENERATOR\v2" "D:\AI-CodeGuard\TECH-INDEX-PY" --format=json

# MessagePack
python tech_index_generator_v22.py "D:\INDEX_GENERATOR\v2" "D:\AI-CodeGuard\TECH-INDEX-PY" --format=msgpack

