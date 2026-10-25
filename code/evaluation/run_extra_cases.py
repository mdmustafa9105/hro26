import csv
import json
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.engine import DeletionAuditEngine

def main():
    extra_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extra_cases")
    req_file = os.path.join(extra_dir, "deletion_requests.csv")
    
    print(f"Loading extra evaluation cases from {req_file}...")
    with open(req_file, "r", encoding="utf-8") as f:
        cases = list(csv.DictReader(f))
        
    print(f"Found {len(cases)} custom cases. Initializing DeletionAuditEngine on {extra_dir}...")
    engine = DeletionAuditEngine(extra_dir)
    
    for c in cases:
        cid = c["case_id"]
        print(f"\n==================================================")
        print(f"Executing {cid}: {c['email']}")
        print(f"Request: {c['request_text']}")
        print(f"Reported: {c['reported_status']} at {c['reported_at']}, Audit At: {c['audit_at']}")
        
        status, steps, unres_reason = engine.audit_case(c)
        print(f"Engine Decision: {status}")
        if unres_reason:
            print(f"Unresolved Reason: {unres_reason}")
        print(f"Emitted Steps ({len(steps)}):")
        for s in steps:
            print(f"  [{s['phase']}] {s['system_id']} {s['resource_id']} {s['operation']} {s['state']} (evidence: '{s.get('evidence_id', '')}')")

if __name__ == "__main__":
    main()
