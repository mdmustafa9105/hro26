import csv
import json
import os
import re
import glob
from typing import Set, Dict, List, Tuple
import pypdf

DATASET_DIR = "dataset"

def gather_dataset_grounded_resources(dataset_dir: str) -> Set[str]:
    """
    Scans all dataset files (excluding sample_output.csv) to collect all
    authentically occurring resource IDs.
    """
    grounded = set()
    res_pattern = re.compile(r'\b(account_\d+|search_\d+|analytics_\d+|support_\d+|export_\d+|data_flow_\d+|backup_\d+|audit_record_\d+|tombstone_\d+)\b', re.I)

    # 1. Scan system_activity.csv
    activity_file = os.path.join(dataset_dir, "system_activity.csv")
    if os.path.exists(activity_file):
        with open(activity_file, "r", encoding="utf-8", errors="ignore") as f:
            for row in csv.DictReader(f):
                r = row.get("resource_id", "").strip().lower()
                if r:
                    grounded.add(r)
                # Also search details
                det = row.get("details", "")
                for m in res_pattern.findall(det):
                    grounded.add(m.lower())

    # 2. Scan all evidence files (text, log, sql, json, pdf, and cached ocr)
    evidence_dir = os.path.join(dataset_dir, "evidence")
    for root, _, files in os.walk(evidence_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            ext = os.path.splitext(fname)[1].lower()
            if ext in (".sql", ".json", ".log", ".txt", ".csv"):
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        for m in res_pattern.findall(content):
                            grounded.add(m.lower())
                except Exception:
                    pass
            elif ext == ".pdf":
                try:
                    reader = pypdf.PdfReader(fpath)
                    for page in reader.pages:
                        text = page.extract_text() or ""
                        for m in res_pattern.findall(text):
                            grounded.add(m.lower())
                except Exception:
                    pass

    # 3. Scan cached parser evidence if available for OCR text
    cache_file = os.path.join("src", "parsers", "evidence_cache.json")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cdata = json.load(f)
                for fid, recs in cdata.items():
                    for rec in recs:
                        rid = rec.get("resource_id", "").strip().lower()
                        if rid:
                            grounded.add(rid)
        except Exception:
            pass

    return grounded

def audit_file(csv_path: str, grounded_resources: Set[str], output_failures_csv: str = None) -> List[Dict[str, str]]:
    failures = []
    total_steps = 0
    grounded_steps = 0
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return failures

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    for row in reader:
        cid = row["case_id"]
        status = row["deletion_status"]
        steps = json.loads(row["steps_json"])

        for step in steps:
            total_steps += 1
            rid = step["resource_id"].strip().lower()
            phase = step["phase"]
            sys_id = step["system_id"]
            op = step["operation"]

            is_grounded = rid in grounded_resources
            
            # Trace or inference check:
            # An account_ or tombstone_ or audit_record_ may be inferred from worker event sequence
            status_label = "GROUNDED" if is_grounded else "NOT_FOUND"

            if not is_grounded:
                failures.append({
                    "case_id": cid,
                    "step_no": str(step["step_no"]),
                    "phase": phase,
                    "system_id": sys_id,
                    "resource_id": rid,
                    "operation": op,
                    "grounding_status": status_label,
                    "reason": f"Resource ID '{rid}' does not appear in raw dataset evidence files or system_activity.csv"
                })
            else:
                grounded_steps += 1

    print(f"\nAudit Results for {csv_path}:")
    print(f"  Total Steps Audited: {total_steps}")
    print(f"  Grounded Steps:      {grounded_steps} ({(grounded_steps/total_steps*100) if total_steps else 0:.2f}%)")
    print(f"  Unfindable Steps:    {len(failures)}")

    if output_failures_csv:
        with open(output_failures_csv, "w", encoding="utf-8", newline="") as f:
            fieldnames = ["case_id", "step_no", "phase", "system_id", "resource_id", "operation", "grounding_status", "reason"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(failures)
        print(f"  Wrote {len(failures)} failure records to {output_failures_csv}")

    return failures

def main():
    print("Collecting grounded resources across all dataset files (excluding sample_output.csv)...")
    grounded = gather_dataset_grounded_resources(DATASET_DIR)
    print(f"Total distinct grounded resource IDs found in dataset: {len(grounded)}")

    # 1. Audit output.csv
    print("\n" + "=" * 60)
    print("AUDITING GROUNDING: output.csv")
    print("=" * 60)
    out_failures = audit_file("output.csv", grounded, "grounding_failures.csv")

    # 2. Audit sample_output.csv
    print("\n" + "=" * 60)
    print("AUDITING GROUNDING: dataset/sample_output.csv")
    print("=" * 60)
    sample_failures = audit_file("dataset/sample_output.csv", grounded)

    if sample_failures:
        print("\nResources in sample_output.csv found nowhere in dataset:")
        unfindable_sample_resources = sorted({f["resource_id"] for f in sample_failures})
        for r in unfindable_sample_resources:
            cases = sorted({f["case_id"] for f in sample_failures if f["resource_id"] == r})
            print(f"  - {r}: cases {cases}")

if __name__ == "__main__":
    main()
