import glob

for f in glob.glob("dataset/evidence/logs/*.log"):
    with open(f, "r", encoding="utf-8") as fh:
        for line in fh:
            if "email_opt_in" in line or "contact_lookup" in line:
                print(f, line.strip())
