with open("dataset/user_identities.csv", "r", encoding="utf-8") as f:
    for line in f:
        if "6645" in line or "5569" in line:
            print("user_identities:", line.strip())

with open("dataset/user_audit_log.csv", "r", encoding="utf-8") as f:
    for line in f:
        if "6645" in line or "5569" in line:
            print("user_audit_log:", line.strip())
