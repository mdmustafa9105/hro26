import os

for root, dirs, files in os.walk("dataset"):
    for f in files:
        if f.endswith((".csv", ".log", ".json", ".sql", ".txt")) and f != "sample_output.csv":
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    if "account_7566" in line:
                        print(f"{path}: {line.strip()[:140]}")
