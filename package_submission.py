import zipfile
import os
from pathlib import Path

def create_code_zip():
    zip_path = Path("code.zip")
    if zip_path.exists():
        zip_path.unlink()

    included_roots = ["README.md", "code", "src", "evaluation"]
    excluded_patterns = ["__pycache__", ".git", ".venv", "venv", ".DS_Store", ".zip", "evidence_cache.json"]

    total_files = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in included_roots:
            p = Path(item)
            if not p.exists():
                print(f"Warning: {p} does not exist!")
                continue
            if p.is_file():
                zf.write(p, arcname=p.name)
                total_files += 1
                print(f"Added file: {p.name}")
            elif p.is_dir():
                for root, dirs, files in os.walk(p):
                    # Filter out directories
                    dirs[:] = [d for d in dirs if not any(ex in d for ex in excluded_patterns)]
                    for f in files:
                        if any(f.endswith(ex) or ex in f for ex in excluded_patterns):
                            continue
                        full_path = Path(root) / f
                        rel_path = full_path.relative_to(Path("."))
                        zf.write(full_path, arcname=str(rel_path))
                        total_files += 1

    print(f"\nSuccessfully created {zip_path} with {total_files} files.")
    print(f"Archive size: {zip_path.stat().st_size / 1024:.2f} KB")

    # Verify contents
    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        print("\nVerifying archive integrity:")
        print(f"Contains 'code/main.py': {'code/main.py' in namelist}")
        print(f"Contains 'README.md': {'README.md' in namelist}")
        print(f"Contains 'evaluation/evaluation_report.md': {'evaluation/evaluation_report.md' in namelist}")
        print(f"Contains 'evaluation/usage_report.md': {'evaluation/usage_report.md' in namelist}")
        print(f"Contains 'code/evaluation/evaluation_report.md': {'code/evaluation/evaluation_report.md' in namelist}")
        print(f"Contains 'code/evaluation/usage_report.md': {'code/evaluation/usage_report.md' in namelist}")
        has_dataset = any('dataset' in name for name in namelist)
        has_pycache = any('__pycache__' in name for name in namelist)
        print(f"Has dataset files (must be False): {has_dataset}")
        print(f"Has __pycache__ files (must be False): {has_pycache}")

if __name__ == "__main__":
    create_code_zip()
