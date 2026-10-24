import sys
import io
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Case 11: novak.tomasz@icloud.com, user_32
from src.parsers.unified_parser import UnifiedEvidenceParser
from src.identity import IdentityResolver

id_res = IdentityResolver('dataset')
ident = id_res.resolve_by_email('novak.tomasz@icloud.com')
print("Ident:", ident)

parser = UnifiedEvidenceParser('dataset')
recs = parser.get_records_for_user(ident, '2026-10-02T11:45:00Z')
print(f"Matched {len(recs)} records for case_11:")
for r in recs:
    print(f"  {r.system_id} | {r.resource_id} | {r.state} | {r.evidence_id} | {r.captured_at}")
