import os

audit_records = [
    "audit_record_4902", "audit_record_6645", "audit_record_5569", 
    "audit_record_4128", "audit_record_7095", "audit_record_3954", "audit_record_1707"
]

for root, dirs, files in os.walk("dataset"):
    for f in files:
        if f.endswith((".csv", ".log", ".json", ".sql", ".txt")) and f != "sample_output.csv":
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                for line_no, line in enumerate(fh, 1):
                    for ar in audit_records:
                        if ar in line:
                            print(f"{path}:{line_no} [{ar}] {line.strip()[:140]}")
