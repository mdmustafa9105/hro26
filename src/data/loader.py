import csv
import json
import os
from datetime import datetime, timezone

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'dataset')
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def parse_ts(s):
    if not s:
        return None
    try:
        # handle Z
        if s.endswith('Z'):
            s = s[:-1] + '+00:00'
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None

def norm_email(e):
    if not e:
        return ''
    return e.strip().lower()

def load_csv(name):
    path = os.path.join(DATA_DIR, name)
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f))

def load_all():
    return {
        'identities': load_csv('user_identities.csv'),
        'audit': load_csv('user_audit_log.csv'),
        'activity': load_csv('system_activity.csv'),
        'rules': load_csv('deletion_rules.csv'),
        'evidence_files': load_csv('evidence_files.csv'),
        'deletion_requests': load_csv('deletion_requests.csv'),
        'sample_requests': load_csv('sample_deletion_requests.csv'),
    }
