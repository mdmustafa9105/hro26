with open("dataset/evidence/logs/resource_lookup_trace_20260926_103856.log", "r", encoding="utf-8") as f:
    for line in f:
        if "l.fontaine46@yahoo.com" in line:
            print(line.strip())
