import json
import os
import re
import csv
#

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_EVIDENCE = os.path.join(ROOT, 'dataset', 'evidence')

class EvidenceParser:
    def __init__(self, evidence_files):
        self.evidence_files = {e['file_id']: e for e in evidence_files}

    def get_path(self, file_id):
        ef = self.evidence_files.get(file_id)
        if not ef:
            return None
        return os.path.join(ROOT, 'dataset', ef['file_path'])

    def parse(self, file_id):
        path = self.get_path(file_id)
        if not path or not os.path.exists(path):
            return {'text': '', 'resources': [], 'idents': []}
        ext = os.path.splitext(path)[1].lower()
        text = ''
        try:
            if ext in ['.json']:
                with open(path, encoding='utf-8') as f:
                    data = json.load(f)
                text = json.dumps(data)
            elif ext in ['.log', '.txt']:
                with open(path, encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            elif ext in ['.sql']:
                with open(path, encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            elif ext in ['.pdf', '.png']:
                # try to read as text if possible? probably not directly; but for now read binary as hex not useful
                try:
                    with open(path, 'rb') as f:
                        data = f.read()
                    text = data[:20000].decode('latin-1', errors='ignore')
                except Exception:
                    text = ''
            else:
                try:
                    with open(path, encoding='utf-8', errors='ignore') as f:
                        text = f.read()
                except Exception:
                    text = ''
        except Exception:
            text = ''
        # extract resources like account_*, search_*, support_*, export_*, analytics_*, backup_*, data_flow_*, audit_record_*
        resources = set(re.findall(r'(account_\d+|search_\d+|support_\d+|export_\d+|analytics_\d+|backup_\d+|data_flow_\d+|audit_record_\d+)', text))
        # emails
        emails = set(re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text.lower()))
        # phones
        phones = set(re.findall(r'\+?\d[\d\s\-\(\)]{7,}\d', text))
        # hashes (long hex)
        hashes = set(re.findall(r'\b[a-f0-9]{40,64}\b', text.lower()))
        return {'text': text, 'resources': list(resources), 'emails': list(emails), 'phones': list(phones), 'hashes': list(hashes), 'path': path}