import asyncio
import os
import re
import sys
import io
from winsdk.windows.storage import StorageFile
from winsdk.windows.graphics.imaging import BitmapDecoder
from winsdk.windows.media.ocr import OcrEngine

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

async def scan_all_images():
    img_dir = os.path.abspath('dataset/evidence/images')
    engine = OcrEngine.try_create_from_user_profile_languages()
    
    for fname in sorted(os.listdir(img_dir)):
        if not fname.endswith('.png'):
            continue
        fpath = os.path.join(img_dir, fname)
        file = await StorageFile.get_file_from_path_async(fpath)
        stream = await file.open_async(0)
        decoder = await BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()
        result = await engine.recognize_async(bitmap)
        text = result.text
        
        resources = re.findall(r'\b(account_\d+|search_\d+|analytics_\d+|support_\d+|export_\d+|data_flow_\d+|backup_\d+|audit_record_\d+|tombstone_\d+)\b', text, re.I)
        emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
        users = re.findall(r'\buser_\d+\b', text, re.I)
        print(f"\n{fname} (len {len(text)}):")
        print("  Resources:", set(r.lower() for r in resources))
        print("  Emails:", set(e.lower() for e in emails))
        print("  Users:", set(u.lower() for u in users))

asyncio.run(scan_all_images())
