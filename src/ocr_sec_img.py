import asyncio
import winsdk.windows.graphics.imaging as imaging
import winsdk.windows.media.ocr as ocr
import winsdk.windows.storage as storage

async def ocr_img():
    path = "d:\\hackerrank-orchestrate-october26\\dataset\\evidence\\images\\security_audit_explorer_20260905.png"
    sf = await storage.StorageFile.get_file_from_path_async(path)
    stream = await sf.open_async(storage.FileAccessMode.READ)
    decoder = await imaging.BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()
    engine = ocr.OcrEngine.try_create_from_user_profile_languages()
    res = await engine.recognize_async(bitmap)
    print("OCR lines for security_audit_explorer:")
    for line in res.lines:
        print(" ", line.text)

asyncio.run(ocr_img())
