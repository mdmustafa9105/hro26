import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.parsers.unified_parser import UnifiedEvidenceParser

parser = UnifiedEvidenceParser("dataset")
for r in parser.all_records:
    if r.resource_id == "data_flow_9846":
        print(r)
