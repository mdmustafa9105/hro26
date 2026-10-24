import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.parsers.unified_parser import UnifiedEvidenceParser

parser = UnifiedEvidenceParser("dataset")
for r in parser.all_records:
    if r.resource_id == "account_4092":
        print(r)
