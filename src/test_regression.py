import unittest
import os
import sys
import csv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine import DeletionAuditEngine
from src.parsers.log_parser import parse_log_file

class DeletionAuditRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = DeletionAuditEngine('dataset')

    def test_evidence_34_account_absence(self):
        """1. A completed lookup or scan event with rows=0 or http_status=404 means ABSENT."""
        recs = self.engine.evidence_parser.records_by_file_id.get('evidence_34', [])
        rec_map = {r.resource_id: r for r in recs}
        
        for acc_id in ['account_7653', 'account_3016', 'account_8590']:
            self.assertIn(acc_id, rec_map, f"{acc_id} missing in evidence_34")
            self.assertEqual(rec_map[acc_id].state, 'ABSENT', f"{acc_id} in evidence_34 must be ABSENT")

    def test_case_363_restore_risk(self):
        """4. Confirm a REPORT_RESTORE_RISK for backup_7253 appears for case_363."""
        with open('dataset/deletion_requests.csv', encoding='utf-8') as f:
            reqs = {r['case_id']: r for r in csv.DictReader(f)}
        
        c363 = reqs.get('case_363')
        self.assertIsNotNone(c363, "case_363 not found in deletion_requests.csv")
        
        status, steps, unres = self.engine.audit_case(c363)
        self.assertEqual(status, 'INCOMPLETE')
        
        restore_findings = [s for s in steps if s['operation'] == 'REPORT_RESTORE_RISK' and s['resource_id'] == 'backup_7253']
        self.assertEqual(len(restore_findings), 1, "Expected exactly 1 REPORT_RESTORE_RISK finding for backup_7253")
        self.assertEqual(restore_findings[0]['state'], 'ACTIVE')
        self.assertEqual(restore_findings[0]['evidence_id'], 'evidence_34')

    def test_case_52_export_decision(self):
        """3. case_52 decides from OCR table row and detail pane that export_1260 is un-deleted (PRESENT)."""
        with open('dataset/deletion_requests.csv', encoding='utf-8') as f:
            reqs = {r['case_id']: r for r in csv.DictReader(f)}
        
        c52 = reqs.get('case_52')
        self.assertIsNotNone(c52, "case_52 not found in deletion_requests.csv")
        
        status, steps, unres = self.engine.audit_case(c52)
        self.assertEqual(status, 'INCOMPLETE')
        
        export_findings = [s for s in steps if s['operation'] == 'REPORT_REMAINING_RECORD' and s['resource_id'] == 'export_1260']
        self.assertEqual(len(export_findings), 1, "Expected REPORT_REMAINING_RECORD finding for export_1260")
        self.assertEqual(export_findings[0]['state'], 'PRESENT')
        self.assertEqual(export_findings[0]['evidence_id'], 'evidence_23')

    def test_temporal_cutoff_rule(self):
        """2. Temporal rule: STATE of resource must come only from evidence captured <= audit_at."""
        with open('dataset/evidence_files.csv', encoding='utf-8') as f:
            file_map = {r['file_id']: r for r in csv.DictReader(f)}
            
        with open('dataset/deletion_requests.csv', encoding='utf-8') as f:
            requests = list(csv.DictReader(f))

        for req in requests:
            status, steps, unres = self.engine.audit_case(req)
            if status == 'COMPLETE':
                audit_at = req['audit_at']
                for s in steps:
                    ev_id = s.get('evidence_id')
                    self.assertTrue(bool(ev_id), f"Case {req['case_id']} is COMPLETE but step has empty evidence_id: {s}")
                    if ev_id in file_map:
                        self.assertLessEqual(file_map[ev_id]['captured_at'], audit_at, 
                                             f"Case {req['case_id']} cites post-audit evidence {ev_id} ({file_map[ev_id]['captured_at']} > {audit_at})")

if __name__ == '__main__':
    unittest.main()
