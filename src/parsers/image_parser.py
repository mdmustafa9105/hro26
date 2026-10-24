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

async def _ocr_image_async(abs_path: str) -> str:
    from winsdk.windows.storage import StorageFile
    from winsdk.windows.graphics.imaging import BitmapDecoder
    engine = _get_ocr_engine()
    if not engine:
        return ""
    file = await StorageFile.get_file_from_path_async(abs_path)
    stream = await file.open_async(0)
    decoder = await BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()
    result = await engine.recognize_async(bitmap)
    return result.text

def parse_image_file(file_id: str, file_path: str, origin: str, captured_at: str) -> List[EvidenceRecord]:
    records: List[EvidenceRecord] = []
    if not os.path.exists(file_path):
        return records

    try:
        text = asyncio.run(_ocr_image_async(os.path.abspath(file_path)))
    except Exception:
        return records

    if not text:
        return records

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
        state = 'PRESENT'

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
            state = 'PRESENT'
        elif r_id_lower.startswith('support_'):
            sys_id = 'support_platform'
            data_cat = 'SUPPORT_MESSAGE'
            state = 'PRESENT'
        elif r_id_lower.startswith('export_'):
            sys_id = 'export_service'
            data_cat = 'USER_EXPORT'
            state = 'PRESENT'
        elif r_id_lower.startswith('search_'):
            sys_id = 'search_service'
            data_cat = 'SEARCH_INDEX_ENTRY'
            state = 'PRESENT'
        elif r_id_lower.startswith('audit_record_'):
            sys_id = 'security_service'
            data_cat = 'SECURITY_AUDIT_LOG'
            state = 'PRESENT'
        elif r_id_lower.startswith('tombstone_'):
            sys_id = 'identity_service'
            data_cat = 'ACCOUNT_TOMBSTONE'
            state = 'PRESENT'

        records.append(EvidenceRecord(
            evidence_id=file_id,
            file_path=file_path,
            captured_at=captured_at,
            origin=origin,
            system_id=sys_id,
            resource_id=r_id_lower,
            data_category=data_cat,
            state=state,
            user_id=list(users)[0].lower() if users else None,
            email=list(emails)[0].lower() if emails else None,
            raw_details={'ocr_text': text[:500]}
        ))

    return records
