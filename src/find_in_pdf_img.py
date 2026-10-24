import glob
import pypdf
import os

pdf_files = glob.glob("dataset/evidence/**/*.pdf", recursive=True)
for p in pdf_files:
    reader = pypdf.PdfReader(p)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    for t in ["audit_record_6645", "audit_record_5569", "6645", "5569"]:
        if t in text:
            print(f"Found {t} in PDF {p}")

print("Checked all PDFs.")
