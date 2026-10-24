import os
import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sql_dir = 'dataset/evidence/databases'
all_schemas = {}

for fname in sorted(os.listdir(sql_dir)):
    if not fname.endswith('.sql'):
        continue
    fpath = os.path.join(sql_dir, fname)
    db = sqlite3.connect(':memory:')
    with open(fpath, 'r', encoding='utf-8') as f:
        db.executescript(f.read())
    tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    for t in tables:
        cols = [r[1] for r in db.execute(f"PRAGMA table_info({t})").fetchall()]
        all_schemas.setdefault(t, set()).update(cols)
    db.close()

print("All SQL Tables and their columns:")
for t, cols in sorted(all_schemas.items()):
    print(f"  {t}: {sorted(cols)}")
