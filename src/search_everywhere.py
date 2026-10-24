import os

targets = ["audit_record_6645", "audit_record_5569"]
for root, dirs, files in os.walk("."):
    if ".git" in root or "node_modules" in root:
        continue
    for f in files:
        if f == "sample_output.csv":
            continue
        path = os.path.join(root, f)
        try:
            with open(path, "rb") as fh:
                data = fh.read()
                for t in targets:
                    if t.encode() in data:
                        print(f"Found {t} in {path}")
        except Exception:
            pass
