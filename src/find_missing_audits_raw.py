import os

targets = [b"audit_record_4902", b"audit_record_6645", b"audit_record_5569"]
for root, dirs, files in os.walk("dataset/evidence"):
    for f in files:
        path = os.path.join(root, f)
        with open(path, "rb") as fh:
            data = fh.read()
            for t in targets:
                if t in data:
                    print(f"Found {t.decode()} in {path}")
