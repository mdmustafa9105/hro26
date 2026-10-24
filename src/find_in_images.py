import glob

png_files = glob.glob("dataset/evidence/**/*.png", recursive=True)
for p in png_files:
    print(p)
