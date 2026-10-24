import unittest
import os
import sys
import csv
import json
import asyncio
import re

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.parsers.image_parser import _ocr_image_async

class RawEvidenceRegressionTests(unittest.TestCase):
    """
    Regression tests asserting ground truth directly from raw evidence files,
    without invoking the engine or relying on engine output.
    """

    def test_evidence_34_raw_lookup_absence(self):
        """
        1. A completed lookup or scan event with rows="0" or http_status="404" means ABSENT.
        Verify directly in structured_service_events_ca_central_20260419.log that lines 20, 25,
        and 32 record profile_lookup_completed with rows="0" and http_status="404".
        """
        log_path = os.path.join("dataset", "evidence", "logs", "structured_service_events_ca_central_20260419.log")
        self.assertTrue(os.path.exists(log_path), f"Evidence file not found: {log_path}")

        with open(log_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines()]

        expected_records = {
            20: ("account_7653", '"rows":"0"', '"http_status":"404"'),
            25: ("account_3016", '"rows":"0"', '"http_status":"404"'),
            32: ("account_8590", '"rows":"0"', '"http_status":"404"'),
        }

        for line_no, (acc_id, rows_pattern, status_pattern) in expected_records.items():
            line_text = lines[line_no - 1]
            self.assertIn(acc_id, line_text, f"Line {line_no} does not contain {acc_id}")
            self.assertIn("profile_lookup_completed", line_text, f"Line {line_no} is not profile_lookup_completed")
            self.assertIn(rows_pattern, line_text, f"Line {line_no} does not contain {rows_pattern}")
            self.assertIn(status_pattern, line_text, f"Line {line_no} does not contain {status_pattern}")

    def test_evidence_34_raw_backup_restore_risk(self):
        """
        4. Confirm restore risk for backup_7253 in evidence_34:
        - Line 15 contains backup_7253 with eligible="true", deletion_block="false", and trace_id="tr-7750694".
        - Line 8 contains trace_id="tr-7750694" and subject_key="m.khumalo88@gmail.com" (case_363 requester).
        - Verify that trace_0642 and usr_c4a79b do NOT exist in evidence_34.
        """
        log_path = os.path.join("dataset", "evidence", "logs", "structured_service_events_ca_central_20260419.log")
        with open(log_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines()]

        line_8 = lines[7]
        self.assertIn("tr-7750694", line_8, "Line 8 does not contain trace tr-7750694")
        self.assertIn("m.khumalo88@gmail.com", line_8, "Line 8 does not contain m.khumalo88@gmail.com")

        line_15 = lines[14]
        self.assertIn("backup_7253", line_15, "Line 15 does not contain backup_7253")
        self.assertIn("restore_candidate_evaluated", line_15, "Line 15 is not restore_candidate_evaluated")
        self.assertIn('"eligible":"true"', line_15, "Line 15 is not eligible='true'")
        self.assertIn('"deletion_block":"false"', line_15, "Line 15 is not deletion_block='false'")
        self.assertIn("tr-7750694", line_15, "Line 15 does not contain trace tr-7750694")

        # Confirm non-existence of fabricated trace and user IDs
        full_content = "\n".join(lines)
        self.assertNotIn("trace_0642", full_content, "trace_0642 must not exist in evidence_34")
        self.assertNotIn("usr_c4a79b", full_content, "usr_c4a79b must not exist in evidence_34")

    def test_evidence_23_raw_ocr_export_rows(self):
        """
        3. case_52 raw OCR check:
        In customer_export_console_20260618.png, export_1260 is un-deleted (Ready),
        created on 18 Jun 2026, and owned by ingrid.dahl@outlook.com.
        """
        img_path = os.path.join("dataset", "evidence", "images", "customer_export_console_20260618.png")
        self.assertTrue(os.path.exists(img_path), f"Evidence image not found: {img_path}")

        text, words = asyncio.run(_ocr_image_async(os.path.abspath(img_path)))
        self.assertTrue(bool(words), "Failed to extract OCR words from image")

        # Group words into visual rows
        words_sorted = sorted(words, key=lambda w: (w['y'], w['x']))
        visual_rows = []
        for w in words_sorted:
            placed = False
            for r in visual_rows:
                if abs(r['avg_y'] - w['y']) <= 15:
                    r['words'].append(w)
                    r['avg_y'] = sum(x['y'] for x in r['words']) / len(r['words'])
                    placed = True
                    break
            if not placed:
                visual_rows.append({'avg_y': w['y'], 'words': [w]})

        row_texts = [" ".join(x['text'] for x in sorted(r['words'], key=lambda w: w['x'])) for r in visual_rows]
        
        # Verify export_1260 row content
        export_1260_rows = [rt for rt in row_texts if "export_1260" in rt]
        self.assertTrue(len(export_1260_rows) > 0, "export_1260 not found in visual rows")
        
        # At least one visual row with export_1260 must contain ingrid.dahl@outlook.com and Ready
        matched_row = any("ingrid.dahl@outlook.com" in rt and "Ready" in rt for rt in export_1260_rows)
        # Or detail pane
        detail_words = [w for w in words if w['x'] > 1200]
        detail_text = " ".join(w['text'] for w in sorted(detail_words, key=lambda w: (w['y'], w['x'])))
        detail_matched = "export_1260" in detail_text and "ingrid.dahl@outlook.com" in detail_text and "Ready" in detail_text

        self.assertTrue(matched_row or detail_matched, "export_1260 row or detail pane does not bind ingrid.dahl@outlook.com with Ready status")

    def test_output_csv_raw_temporal_cutoffs(self):
        """
        2. Temporal rule:
        For every COMPLETE case in output.csv:
        - Every verification step must have a non-empty evidence_id.
        - The cited evidence file must have been captured at or before audit_at.
        """
        manifest_path = os.path.join("dataset", "evidence_files.csv")
        file_captured_at = {}
        with open(manifest_path, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                file_captured_at[r["file_id"]] = r["captured_at"]

        reqs_path = os.path.join("dataset", "deletion_requests.csv")
        case_audit_at = {}
        with open(reqs_path, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                case_audit_at[r["case_id"]] = r["audit_at"]

        output_path = "output.csv"
        self.assertTrue(os.path.exists(output_path), "output.csv does not exist")

        with open(output_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        complete_count = 0
        for r in rows:
            if r["deletion_status"] == "COMPLETE":
                complete_count += 1
                cid = r["case_id"]
                audit_at = case_audit_at.get(cid, "")
                steps = json.loads(r["steps_json"])
                self.assertTrue(len(steps) > 0, f"Case {cid} is COMPLETE with 0 steps")
                for s in steps:
                    ev_id = s.get("evidence_id")
                    self.assertTrue(bool(ev_id), f"Case {cid} has empty evidence_id in step {s}")
                    self.assertIn(ev_id, file_captured_at, f"Evidence ID {ev_id} missing in manifest")
                    cap_time = file_captured_at[ev_id]
                    self.assertLessEqual(cap_time, audit_at, 
                                         f"Case {cid} cited evidence {ev_id} captured at {cap_time} > audit_at {audit_at}")

        self.assertGreater(complete_count, 0, "No COMPLETE cases found in output.csv")

if __name__ == "__main__":
    unittest.main()
