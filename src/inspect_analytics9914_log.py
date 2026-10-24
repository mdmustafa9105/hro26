with open("dataset/evidence/logs/service_events_ap_south_20260915.log", "r", encoding="utf-8") as f:
    for line in f:
        if "analytics_9914" in line:
            print(line.strip())
