import re
from collections import Counter

events = Counter()
with open("dataset/evidence/logs/service_events_ap_south_20260915.log", "r", encoding="utf-8") as f:
    for line in f:
        m = re.search(r'\bevent=([a-zA-Z0-9_\-]+)', line)
        if m:
            events[m.group(1)] += 1

for ev, count in events.most_common():
    print(f"{ev}: {count}")
