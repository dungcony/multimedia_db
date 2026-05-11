from ..models.mvideo import MVideo
import os
import csv
import time
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

CSV_PATH = str(PROJECT_ROOT / os.getenv("CSV_PATH", ""))


def read_urls_from_csv(filepath):
    print(f"  Reading URLs from CSV: {filepath}")
    urls = []
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                urls.append(row[0])
    return urls


def get_video(cnn=None):
    urls = read_urls_from_csv(CSV_PATH)
    print(f"  Found {len(urls)} URLs from CSV")

    mvideos = []
    for i, url in enumerate(urls, 1):
        short_url = url.split("/")[-1]
        print(f"  [{i}/{len(urls)}] Processing {short_url}...", end=" ", flush=True)
        t0 = time.time()
        try:
            mv = MVideo(url, cnn=cnn)
            t1 = time.time()
            print(
                f"OK "
                f"frames={mv.frame_count}, "
                f"keyframes={len(mv.frames)}, "
                f"time={t1 - t0:.1f}s"
            )
            mvideos.append(mv)
        except Exception as e:
            print(f"  [{i}/{len(urls)}] FAILED: {e}")

    print(f"  Loaded {len(mvideos)}/{len(urls)} videos successfully")
    return mvideos
