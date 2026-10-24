test_emails = [
    'minjun.kim@gmail.com', 'lucia-torres@gmail.com', 
    'leonie.g9352@outlook.com', 'e.varga90@yahoo.com'
]

with open('dataset/evidence/logs/service_events_ap_south_20260915.log', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines in evidence_01: {len(lines)}")
for email in test_emails:
    print(f"\n--- Matches for {email} ---")
    matched_traces = set()
    for l in lines:
        if email in l:
            print("Direct:", l.strip())
            # extract trace id if present
            parts = [p.strip() for p in l.split('|')]
            if len(parts) > 3 and parts[3].startswith('tr-'):
                matched_traces.add(parts[3])
    for tr in matched_traces:
        print(f" Trace {tr}:")
        for l in lines:
            if tr in l:
                print("   ", l.strip())
