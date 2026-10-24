import csv
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

evidence_csv = os.path.join('dataset', 'evidence_files.csv')

extensions = {}
file_types = {'pdf': 0, 'image': 0, 'sql': 0, 'json': 0, 'log': 0, 'txt': 0, 'other': 0}
image_exts = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff'}

pdf_files = []
image_files = []

with open(evidence_csv, mode='r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        file_id = row['file_id']
        file_path = row['file_path']
        ext = os.path.splitext(file_path)[1].lower()
        extensions[ext] = extensions.get(ext, 0) + 1
        
        if ext == '.pdf':
            file_types['pdf'] += 1
            pdf_files.append((file_id, file_path, row.get('origin', ''), row.get('captured_at', '')))
        elif ext in image_exts:
            file_types['image'] += 1
            image_files.append((file_id, file_path, row.get('origin', ''), row.get('captured_at', '')))
        elif ext == '.sql':
            file_types['sql'] += 1
        elif ext == '.json':
            file_types['json'] += 1
        elif ext == '.log':
            file_types['log'] += 1
        elif ext == '.txt':
            file_types['txt'] += 1
        else:
            file_types['other'] += 1

print(f"Total evidence files in manifest: {sum(extensions.values())}")
print("Extension breakdown:")
for ext, count in sorted(extensions.items(), key=lambda x: -x[1]):
    print(f"  {ext}: {count}")

print(f"\nPDF files count: {len(pdf_files)}")
for p in pdf_files:
    print(f"  {p}")

print(f"\nImage files count: {len(image_files)}")
for img in image_files:
    print(f"  {img}")
