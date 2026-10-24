import glob
import os

files = glob.glob("dataset/evidence/**/*.txt", recursive=True)
for f in files:
    print(f, os.path.getsize(f))
    with open(f, "r", encoding="utf-8") as fh:
        lines = fh.readlines()
        print(f"  Lines: {len(lines)}")
        for l in lines[:5]:
            print("   ", l.strip())
