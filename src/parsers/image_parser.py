import asyncio
import os
import re
from typing import List
from src.models import EvidenceRecord

_OCR_ENGINE = None

def _get_ocr_engine():
    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        try:
            from winsdk.windows.media.ocr import OcrEngine
            _OCR_ENGINE = OcrEngine.try_create_from_user_profile_languages()
        except Exception:
            _OCR_ENGINE = False
    return _OCR_ENGINE

async def _ocr_image_async(abs_path: str):
    from winsdk.windows.storage import StorageFile
    from winsdk.windows.graphics.imaging import BitmapDecoder
    engine = _get_ocr_engine()
    if not engine:
        return "", []
    file = await StorageFile.get_file_from_path_async(abs_path)
    stream = await file.open_async(0)
    decoder = await BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()
    result = await engine.recognize_async(bitmap)
    
    words = []
    for line in result.lines:
        for w in line.words:
            words.append({
                'text': w.text,
                'x': w.bounding_rect.x,
                'y': w.bounding_rect.y,
                'w': w.bounding_rect.width,
                'h': w.bounding_rect.height
            })
    return result.text, words

def parse_image_file(file_id: str, file_path: str, origin: str, captured_at: str) -> List[EvidenceRecord]:
    records: List[EvidenceRecord] = []
    if not os.path.exists(file_path):
        return records

    try:
        text, words = asyncio.run(_ocr_image_async(os.path.abspath(file_path)))
    except Exception:
        return records

    if not text:
        return records

    # Visual row grouping from bounding boxes
    row_bindings = {}
    row_states = {}
    if words:
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

        for r in visual_rows:
            r_words = sorted(r['words'], key=lambda x: x['x'])
            row_str = " ".join(x['text'] for x in r_words)
            res_matches = re.findall(r'\b(account_\d+|search_\d+|analytics_\d+|support_\d+|export_\d+|data_flow_\d+|backup_\d+|audit_record_\d+|tombstone_\d+)\b', row_str, re.I)
            email_matches = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', row_str)
            if res_matches and email_matches:
                for rm in res_matches:
                    r_id_l = rm.lower()
                    row_bindings[r_id_l] = email_matches[0].lower()
                    if any(s in row_str for s in ['Ready', 'Collecting', 'Packaging', 'Delivered']):
                        row_states[r_id_l] = 'PRESENT'
                    elif any(s in row_str for s in ['Deleted', 'Removed', 'Not Found']):
                        row_states[r_id_l] = 'ABSENT'

        # Check detail pane (x > 1200)
        detail_words = [w for w in words if w['x'] > 1200]
        if detail_words:
            detail_str = " ".join(w['text'] for w in sorted(detail_words, key=lambda w: (w['y'], w['x'])))
            d_res = re.findall(r'\b(account_\d+|search_\d+|analytics_\d+|support_\d+|export_\d+|data_flow_\d+|backup_\d+|audit_record_\d+|tombstone_\d+)\b', detail_str, re.I)
            d_em = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', detail_str)
            if d_res and d_em:
                for drm in d_res:
                    row_bindings[drm.lower()] = d_em[0].lower()
                    if 'Ready' in detail_str:
                        row_states[drm.lower()] = 'PRESENT'

    resources = set(re.findall(r'\b(account_\d+|search_\d+|analytics_\d+|support_\d+|export_\d+|data_flow_\d+|backup_\d+|audit_record_\d+|tombstone_\d+)\b', text, re.I))
    emails = set(re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text))
    users = set(re.findall(r'\buser_\d+\b', text, re.I))

    # Detect state keywords in screenshot text
    is_active = bool(re.search(r'\b(Active|Enabled|Running|Connected)\b', text, re.I))
    is_blocked = bool(re.search(r'\b(Blocked|Denied|Disabled)\b', text, re.I))

    # For each resource found:
    for r_id in resources:
        r_id_lower = r_id.lower()
        sys_id = origin
        data_cat = 'USER_PROFILE'
        state = row_states.get(r_id_lower, 'PRESENT')

        if r_id_lower.startswith('data_flow_'):
            sys_id = 'integration_service'
            data_cat = 'DATA_FLOW'
            state = 'ACTIVE' if is_active else 'DISABLED'
        elif r_id_lower.startswith('backup_'):
            sys_id = 'backup_service'
            data_cat = 'BACKUP_ARCHIVE'
            state = 'BLOCKED' if is_blocked else 'ACTIVE'
        elif r_id_lower.startswith('analytics_'):
            sys_id = 'analytics_platform'
            data_cat = 'ANALYTICS_PROFILE'
            state = row_states.get(r_id_lower, 'PRESENT')
        elif r_id_lower.startswith('support_'):
            sys_id = 'support_platform'
            data_cat = 'SUPPORT_MESSAGE'
            state = row_states.get(r_id_lower, 'PRESENT')
        elif r_id_lower.startswith('export_'):
            sys_id = 'export_service'
            data_cat = 'USER_EXPORT'
            state = row_states.get(r_id_lower, 'PRESENT')
        elif r_id_lower.startswith('search_'):
            sys_id = 'search_service'
            data_cat = 'SEARCH_INDEX_ENTRY'
            state = row_states.get(r_id_lower, 'PRESENT')
        elif r_id_lower.startswith('audit_record_'):
            sys_id = 'security_service'
            data_cat = 'SECURITY_AUDIT_LOG'
            state = 'PRESENT'
        elif r_id_lower.startswith('tombstone_'):
            sys_id = 'identity_service'
            data_cat = 'ACCOUNT_TOMBSTONE'
            state = 'PRESENT'

        # Associate owner: prefer row binding if available
        best_email = row_bindings.get(r_id_lower)
        if not best_email and emails:
            r_pos = text.lower().find(r_id_lower)
            email_matches = [(m.start(), m.group().lower()) for m in re.finditer(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)]
            best_email = min(email_matches, key=lambda em: (0 if em[0] >= r_pos else 1, abs(em[0] - r_pos)))[1]

        best_user = None
        if users:
            r_pos = text.lower().find(r_id_lower)
            user_matches = [(m.start(), m.group().lower()) for m in re.finditer(r'\buser_\d+\b', text, re.I)]
            best_user = min(user_matches, key=lambda um: (0 if um[0] >= r_pos else 1, abs(um[0] - r_pos)))[1]

        records.append(EvidenceRecord(
            evidence_id=file_id,
            file_path=file_path,
            captured_at=captured_at,
            origin=origin,
            system_id=sys_id,
            resource_id=r_id_lower,
            data_category=data_cat,
            state=state,
            user_id=best_user,
            email=best_email,
            raw_details={'ocr_text': text[:500]}
        ))

    return records
