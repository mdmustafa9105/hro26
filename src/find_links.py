import os
import glob

search_terms = ["account_3136", "account_5684", "analytics_1895", "analytics_4566", "account_5334"]

print("Searching across dataset/...")
for root, dirs, files in os.walk("dataset"):
    for f in files:
        if f.endswith((".csv", ".log", ".json", ".sql", ".txt")):
            path = os.path.join(root, f)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    content = fh.read()
                    for term in search_terms:
                        if term in content:
                            print(f"Found '{term}' in {path}")
            except Exception:
                pass
