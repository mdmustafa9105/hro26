with open("dataset/evidence/logs/service_events_ap_south_20260915.log", "r", encoding="utf-8") as f:
    for line in f:
        if "account_4092" in line:
            print(line.strip())
