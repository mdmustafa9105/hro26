import csv
import json
import os
from typing import Dict, List
from src.models import EvidenceRecord
from src.parsers.sql_parser import parse_sql_file
from src.parsers.json_parser import parse_json_file
from src.parsers.text_parser import parse_text_file
from src.parsers.log_parser import parse_log_file
from src.parsers.pdf_parser import parse_pdf_file
from src.parsers.image_parser import parse_image_file

CACHE_FILE = os.path.join(os.path.dirname(__file__), 'evidence_cache.json')

class UnifiedEvidenceParser:
    def __init__(self, dataset_dir: str):
        self.dataset_dir = dataset_dir
        self.records_by_file_id: Dict[str, List[EvidenceRecord]] = {}
        self.all_records: List[EvidenceRecord] = []
        self.file_captured_at: Dict[str, str] = {}
        manifest_path = os.path.join(self.dataset_dir, 'evidence_files.csv')
        if os.path.exists(manifest_path):
            with open(manifest_path, mode='r', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    self.file_captured_at[row['file_id']] = row.get('captured_at', '')
        self._load_and_parse_all()

    def _load_and_parse_all(self):
        # Check if cache exists
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                for file_id, rec_list in cached_data.items():
                    recs = [EvidenceRecord(**r) for r in rec_list]
                    self.records_by_file_id[file_id] = recs
                    self.all_records.extend(recs)
                return
            except Exception:
                pass

        manifest_path = os.path.join(self.dataset_dir, 'evidence_files.csv')
        with open(manifest_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            manifest = list(reader)

        cache_dict = {}
        for row in manifest:
            file_id = row['file_id']
            rel_path = row['file_path']
            origin = row.get('origin', '')
            captured_at = row.get('captured_at', '')
            full_path = os.path.join(self.dataset_dir, rel_path)

            ext = os.path.splitext(full_path)[1].lower()
            recs: List[EvidenceRecord] = []
            if ext == '.sql':
                recs = parse_sql_file(file_id, full_path, origin, captured_at)
            elif ext == '.json':
                recs = parse_json_file(file_id, full_path, origin, captured_at)
            elif ext == '.txt':
                recs = parse_text_file(file_id, full_path, origin, captured_at)
            elif ext == '.log':
                recs = parse_log_file(file_id, full_path, origin, captured_at)
            elif ext == '.pdf':
                recs = parse_pdf_file(file_id, full_path, origin, captured_at)
            elif ext in ('.png', '.jpg', '.jpeg'):
                recs = parse_image_file(file_id, full_path, origin, captured_at)

            self.records_by_file_id[file_id] = recs
            self.all_records.extend(recs)
            cache_dict[file_id] = [r.__dict__ for r in recs]

        # Save cache
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache_dict, f, indent=2)
        except Exception:
            pass

    def get_records_for_user(self, identity, cutoff_time: str) -> List[EvidenceRecord]:
        matched = []
        for r in self.all_records:
            if r.captured_at <= cutoff_time:
                if r.links_to_user(identity):
                    matched.append(r)
        return matched
