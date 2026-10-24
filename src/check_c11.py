import sys
import os
import io
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from src.engine import DeletionAuditEngine

engine = DeletionAuditEngine('dataset')
with open('dataset/sample_deletion_requests.csv', mode='r', encoding='utf-8') as f:
    c11 = next(r for r in csv.DictReader(f) if r['case_id'] == 'case_11')
with open('dataset/sample_output.csv', mode='r', encoding='utf-8') as f:
    c11_exp = next(r for r in csv.DictReader(f) if r['case_id'] == 'case_11')

st, steps, _ = engine.audit_case(c11)
exp_steps = json.loads(c11_exp['steps_json'])
print('Status match:', st == c11_exp['deletion_status'])
print('Steps match:', steps == exp_steps)
if steps != exp_steps:
    print('Steps count pred:', len(steps), 'exp:', len(exp_steps))
    for i in range(max(len(steps), len(exp_steps))):
        p = steps[i] if i < len(steps) else None
        e = exp_steps[i] if i < len(exp_steps) else None
        print(f"Step {i+1}:")
        print(f"  Pred: {p}")
        print(f"  Exp:  {e}")
