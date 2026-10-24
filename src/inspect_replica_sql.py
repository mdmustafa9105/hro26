import sqlite3
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

db = sqlite3.connect(':memory:')
with open('dataset/evidence/databases/customer_data_failover_replica_20260920.sql', 'r', encoding='utf-8') as f:
    db.executescript(f.read())

for t in ['customer_data_primary', 'customer_data_failover_replica']:
    rows = db.execute(f"SELECT * FROM {t} LIMIT 3").fetchall()
    print(f"Table {t} sample rows:")
    for r in rows:
        print(" ", r[0], r[1], r[2], r[3][:100] if len(r) > 3 and r[3] else "")
