import os
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

with open('dataset/evidence/logs/resource_lookup_trace_20260728_054417.log', 'r', encoding='utf-8') as f:
    for _ in range(10):
        print(f.readline().strip())
