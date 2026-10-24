import os
import json
import sqlite3
import tempfile
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Inspect JSON files
json_dir = 'dataset/evidence/records'
json_keys = {}
for fname in sorted(os.listdir(json_dir)):
    if not fname.endswith('.json'):
        continue
    fpath = os.path.join(json_dir, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        try:
            d = json.load(f)
            keys = tuple(sorted(d.keys()))
            json_keys[keys] = json_keys.get(keys, []) + [fname]
        except Exception as e:
            print('JSON error in', fname, e)

print("JSON file top-level structures:")
for keys, fnames in json_keys.items():
    print(f"  Keys: {keys} -> {len(fnames)} files (e.g. {fnames[0]})")

# Inspect SQL files
sql_dir = 'dataset/evidence/databases'
print("\nSQL files:")
sql_tables = {}
for fname in sorted(os.listdir(sql_dir)):
    if not fname.endswith('.sql'):
        continue
    fpath = os.path.join(sql_dir, fname)
    # create temp sqlite db
    db = sqlite3.connect(':memory:')
    with open(fpath, 'r', encoding='utf-8') as f:
        sql = f.read()
    try:
        db.executescript(sql)
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        sql_tables[tuple(sorted(tables))] = sql_tables.get(tuple(sorted(tables)), []) + [fname]
    except Exception as e:
        print('SQL error in', fname, e)
    db.close()

print("SQL file tables:")
for tables, fnames in sql_tables.items():
    print(f"  Tables: {tables} -> {len(fnames)} files (e.g. {fnames[0]})")

# Inspect LOG files
log_dir = 'dataset/evidence/logs'
print("\nLOG files count:", len(os.listdir(log_dir)))
for fname in sorted(os.listdir(log_dir))[:5]:
    fpath = os.path.join(log_dir, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
    print(f"  {fname}: {first_line[:100]}")
