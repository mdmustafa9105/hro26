import pypdf
import os
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

pdf_dir = 'dataset/evidence/documents'
for fname in sorted(os.listdir(pdf_dir)):
    if not fname.endswith('.pdf'):
        continue
    fpath = os.path.join(pdf_dir, fname)
    reader = pypdf.PdfReader(fpath)
    text = ""
    for p in reader.pages:
        text += (p.extract_text() or "") + "\n"
    
    print(f"\n=== {fname} ===")
    resources = re.findall(r'\b(account_\d+|search_\d+|analytics_\d+|support_\d+|export_\d+|data_flow_\d+|backup_\d+|audit_record_\d+|tombstone_\d+)\b', text)
    emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
    users = re.findall(r'\buser_\d+\b', text)
    print("Resources:", set(resources))
    print("Emails:", set(emails))
    print("Users:", set(users))
    print("Snippet:", text[:250].replace('\n', ' '))
