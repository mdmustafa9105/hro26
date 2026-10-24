import os

for root, dirs, files in os.walk("dataset"):
    for f in files:
        if f.endswith((".csv", ".log", ".json", ".sql", ".txt")) and f != "sample_output.csv":
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                for line_no, line in enumerate(fh, 1):
                    if "data_flow_9846" in line:
                        print(f"{path}:{line_no} {line.strip()[:140]}")
