import os
import json
import sqlite3
import csv
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 1. Snapshots bundle JSON
with open('dataset/evidence/records/customer_data_snapshot_bundle_20260131.json', 'r', encoding='utf-8') as f:
    bundle = json.load(f)
print("--- Snapshot Bundle Collections ---")
for s in bundle.get('snapshots', []):
    data_store = s.get('data_store')
    coll = s.get('collection')
    recs = s.get('records', [])
    first_rec = recs[0] if recs else {}
    print(f"Store: {data_store}, Coll: {coll}, count: {len(recs)}, keys: {list(first_rec.keys())}")

# 2. Service exports JSON
with open('dataset/evidence/records/service_resource_export_20260129_114459.json', 'r', encoding='utf-8') as f:
    exports = json.load(f)
print("\n--- Service Exports Systems ---")
for sys_id, content in exports.get('service_exports', {}).items():
    print(f"System: {sys_id}, content keys: {list(content.keys())}")
    for k, v in content.items():
        if isinstance(v, list) and v:
            print(f"  {k} (list len {len(v)}): sample keys: {list(v[0].keys()) if isinstance(v[0], dict) else type(v[0])}")
        elif isinstance(v, dict):
            print(f"  {k} (dict): sample keys: {list(v.keys())}")

# 3. Connector configs JSON
with open('dataset/evidence/records/connector_configurations_20260812.json', 'r', encoding='utf-8') as f:
    connectors = json.load(f)
print("\n--- Connector Configs ---")
recs = connectors.get('records', [])
if recs:
    print(f"Connector record keys: {list(recs[0].keys())}")
    print(f"Sample: {recs[0]}")

# 4. Analytics reports JSON
with open('dataset/evidence/records/customer_analytics_report_20260907.json', 'r', encoding='utf-8') as f:
    an = json.load(f)
print("\n--- Analytics Report ---")
recs = an.get('records', [])
if recs:
    print(f"Analytics record keys: {list(recs[0].keys())}")
    print(f"Sample: {recs[0]}")
