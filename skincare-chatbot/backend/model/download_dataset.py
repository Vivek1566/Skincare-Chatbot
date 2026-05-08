"""
Fast image downloader v2 - Fill remaining gaps using bing_image_downloader.
Only downloads for classes that have < 100 images.
"""
import os
import sys
import hashlib
import shutil
from pathlib import Path

def install_package(pkg):
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', pkg])

try:
    from bing_image_downloader import downloader
except ImportError:
    install_package('bing-image-downloader')
    from bing_image_downloader import downloader

from PIL import Image

DATASET_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / 'dataset'
TARGET = 100

QUERIES = {
    'dry': [
        'dry skin face dermatology',
        'dry flaky skin on face',
        'dehydrated dry facial skin',
        'dry skin face woman closeup',
        'dry cracked skin face treatment',
        'dry skin face man',
        'xerosis dry skin face',
        'extremely dry face skin',
    ],
    'redness': [
        'facial redness skin',
        'rosacea face skin',
        'red face skin irritation',
        'facial redness closeup',
        'skin redness cheeks face',
        'irritated red skin face woman',
        'redness face dermatology condition',
        'red irritated facial skin',
    ],
    'oily': [
        'oily skin face closeup',
        'oily shiny face skin',
        'oily skin face woman',
        'greasy oily face',
        'oily skin face man',
        'oily t zone face',
        'sebaceous oily skin face',
        'very oily face skin',
    ],
    'normal': [
        'normal healthy skin face',
        'clear skin face closeup',
        'healthy face skin',
        'smooth skin face woman',
        'normal complexion face',
        'healthy skin face man',
        'clear complexion face closeup',
        'good skin face',
    ],
    'acne': [
        'acne face skin condition',
        'pimples face closeup skin',
    ],
    'bags': [
        'under eye bags face',
        'dark circles eyes face',
    ],
}


def count_images(class_dir):
    """Count all image files recursively."""
    count = 0
    for f in class_dir.rglob('*'):
        if f.is_file() and f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.bmp', '.gif'):
            count += 1
    return count


def cleanup_temp_dirs(class_dir):
    """Remove temporary download subdirectories from icrawler."""
    for item in class_dir.iterdir():
        if item.is_dir() and item.name.startswith('_temp'):
            shutil.rmtree(item, ignore_errors=True)


def move_from_subdirs(class_dir, class_name):
    """Move images from subdirectories (numbered dirs, bing dirs) to root of class dir."""
    for subdir in list(class_dir.iterdir()):
        if subdir.is_dir():
            for img in subdir.rglob('*'):
                if img.is_file() and img.suffix.lower() in ('.jpg', '.jpeg', '.png', '.bmp', '.gif'):
                    # Create unique name
                    with open(img, 'rb') as f:
                        fhash = hashlib.md5(f.read()).hexdigest()[:12]
                    new_name = f"{class_name}_{fhash}{img.suffix}"
                    dest = class_dir / new_name
                    if not dest.exists():
                        try:
                            shutil.copy2(str(img), str(dest))
                        except:
                            pass
            # Remove the subdirectory
            shutil.rmtree(subdir, ignore_errors=True)


def validate_images(class_dir):
    """Remove corrupted or tiny images."""
    removed = 0
    for img_file in list(class_dir.iterdir()):
        if not img_file.is_file():
            continue
        if img_file.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.bmp', '.gif'):
            img_file.unlink()
            continue
        try:
            with Image.open(img_file) as img:
                img.verify()
            with Image.open(img_file) as img:
                w, h = img.size
                if w < 50 or h < 50:
                    img_file.unlink()
                    removed += 1
        except Exception:
            try:
                img_file.unlink()
                removed += 1
            except:
                pass
    return removed


def download_for_class(class_name, queries, needed):
    """Download images for a specific class."""
    class_dir = DATASET_DIR / class_name
    class_dir.mkdir(parents=True, exist_ok=True)

    per_query = max(needed // len(queries) + 5, 15)
    temp_base = DATASET_DIR / f'_bing_temp_{class_name}'

    for qi, query in enumerate(queries):
        current = count_images(class_dir)
        if current >= TARGET:
            break

        print(f"    [{qi+1}/{len(queries)}] '{query}' (fetching {per_query})...")

        try:
            downloader.download(
                query,
                limit=per_query,
                output_dir=str(temp_base),
                adult_filter_off=False,
                force_replace=False,
                timeout=10,
                verbose=False,
            )
        except Exception as e:
            print(f"      [WARN] {e}")
            continue

        # Move downloaded images to class directory
        for subdir in temp_base.rglob('*'):
            if subdir.is_file() and subdir.suffix.lower() in ('.jpg', '.jpeg', '.png', '.bmp', '.gif'):
                with open(subdir, 'rb') as f:
                    fhash = hashlib.md5(f.read()).hexdigest()[:12]
                new_name = f"{class_name}_{fhash}{subdir.suffix}"
                dest = class_dir / new_name
                if not dest.exists():
                    try:
                        shutil.copy2(str(subdir), str(dest))
                    except:
                        pass

    # Cleanup temp
    if temp_base.exists():
        shutil.rmtree(temp_base, ignore_errors=True)


def main():
    print("=" * 60)
    print("FAST IMAGE DOWNLOADER v2")
    print("=" * 60)

    # First, consolidate existing images from subdirectories
    print("\n[STEP 1] Consolidating existing images...")
    for class_name in QUERIES:
        class_dir = DATASET_DIR / class_name
        if class_dir.exists():
            cleanup_temp_dirs(class_dir)
            move_from_subdirs(class_dir, class_name)
            removed = validate_images(class_dir)
            count = count_images(class_dir)
            print(f"  {class_name}: {count} valid images (removed {removed} invalid)")

    # Download missing images
    print(f"\n[STEP 2] Downloading missing images (target: {TARGET} per class)...")
    for class_name, queries in QUERIES.items():
        class_dir = DATASET_DIR / class_name
        current = count_images(class_dir)
        needed = TARGET - current

        if needed <= 0:
            print(f"\n  [SKIP] {class_name}: already has {current} images ✓")
            continue

        print(f"\n  [DOWNLOAD] {class_name}: need {needed} more (have {current})...")
        download_for_class(class_name, queries, needed)

        # Validate new downloads
        validate_images(class_dir)
        final = count_images(class_dir)
        print(f"  [DONE] {class_name}: {final} images total")

    # Final summary
    print(f"\n{'=' * 60}")
    print("FINAL DATASET SUMMARY")
    print(f"{'=' * 60}")
    total = 0
    for class_name in sorted(QUERIES.keys()):
        class_dir = DATASET_DIR / class_name
        count = count_images(class_dir) if class_dir.exists() else 0
        total += count
        status = "✓" if count >= TARGET else f"⚠ (need {TARGET - count} more)"
        print(f"  {class_name:>10}: {count:>4} images {status}")
    print(f"  {'TOTAL':>10}: {total:>4} images")
    print("=" * 60)


if __name__ == '__main__':
    main()
