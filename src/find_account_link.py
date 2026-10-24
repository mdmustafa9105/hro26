import os

targets = ["account_3136", "account_3677", "account_4857", "account_8858", "account_5037"]

for root, dirs, files in os.walk("dataset"):
    for f in files:
        if f.endswith((".csv", ".log", ".json", ".sql", ".txt")) and f != "sample_output.csv":
            path = os.path.join(root, f)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    for line_no, line in enumerate(fh, 1):
                        for t in targets:
                            if t in line:
                                print(f"{path}:{line_no} [{t}] {line.strip()[:150]}")
            except Exception:
                pass
