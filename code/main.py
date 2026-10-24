import csv
import json
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine import DeletionAuditEngine

def run(dataset_dir="dataset", output_csv="output.csv"):
    requests_path = os.path.join(dataset_dir, "deletion_requests.csv")
    if not os.path.exists(requests_path):
        print(f"Error: {requests_path} not found.")
        sys.exit(1)

    print(f"Loading deletion requests from {requests_path}...")
    with open(requests_path, "r", encoding="utf-8") as f:
        requests = list(csv.DictReader(f))

    print(f"Found {len(requests)} evaluation cases.")
    print("Initializing DeletionAuditEngine...")
    engine = DeletionAuditEngine(dataset_dir)

    results = []
    unresolved_cases = []

    print("Auditing cases...")
    for idx, req in enumerate(requests, start=1):
        case_id = req["case_id"]
        status, steps, unres_reason = engine.audit_case(req)

        if unres_reason:
            unresolved_cases.append({
                "case_id": case_id,
                "email": req.get("email", ""),
                "reason": unres_reason
            })

        results.append({
            "case_id": case_id,
            "deletion_status": status,
            "steps_json": json.dumps(steps, separators=(',', ':'))
        })

        if idx % 50 == 0 or idx == len(requests):
            print(f"  Processed {idx}/{len(requests)} cases...")

    # Sort results strictly by case_id
    results.sort(key=lambda r: int(r["case_id"].split("_")[1]) if "_" in r["case_id"] and r["case_id"].split("_")[1].isdigit() else r["case_id"])

    # Write output.csv at root
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "deletion_status", "steps_json"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nWrote {len(results)} rows to {output_csv}.")

    if unresolved_cases:
        with open("unresolved.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["case_id", "email", "reason"])
            writer.writeheader()
            writer.writerows(unresolved_cases)
        print(f"Wrote {len(unresolved_cases)} unresolved cases to unresolved.csv.")
    else:
        print("Zero unresolved cases.")

if __name__ == "__main__":
    run()
