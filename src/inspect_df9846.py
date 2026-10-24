with open("dataset/evidence/logs/service_events_ap_south_20260915.log", "r", encoding="utf-8") as f:
    for line in f:
        if "data_flow_9846" in line or "data_flow_1121" in line:
            print(line.strip())
