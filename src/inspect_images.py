import os
import sys
import io
from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

image_dir = 'dataset/evidence/images'
for fname in sorted(os.listdir(image_dir)):
    if not fname.endswith('.png'):
        continue
    fpath = os.path.join(image_dir, fname)
    img = Image.open(fpath)
    print(f"{fname}: size={img.size}, mode={img.mode}, format={img.format}")
