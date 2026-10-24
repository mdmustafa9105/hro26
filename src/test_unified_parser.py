import sys
import os
import io
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.parsers.unified_parser import UnifiedEvidenceParser

t0 = time.time()
parser = UnifiedEvidenceParser('dataset')
t1 = time.time()

print(f"Loaded UnifiedEvidenceParser in {t1 - t0:.2f} seconds")
print(f"Total evidence files parsed: {len(parser.records_by_file_id)}")
print(f"Total normalized evidence records: {len(parser.all_records)}")

# Breakdown by system
by_sys = {}
by_state = {}
for r in parser.all_records:
    by_sys[r.system_id] = by_sys.get(r.system_id, 0) + 1
    by_state[r.state] = by_state.get(r.state, 0) + 1

print("\nRecords by system:")
for s, c in sorted(by_sys.items()):
    print(f"  {s}: {c}")

print("\nRecords by state:")
for st, c in sorted(by_state.items()):
    print(f"  {st}: {c}")
