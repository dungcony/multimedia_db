from ..models.mvideo import MVideo
import os
import csv
from pathlib import Path
from dotenv import load_dotenv

# Thư mục gốc project: src/services/../../ = project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

CSV_PATH = str(PROJECT_ROOT / os.getenv("CSV_PATH", ""))


def read_urls_from_csv(filepath):
    urls = []
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:  # bỏ qua dòng trống
                urls.append(row[0])
    return urls

def get_video():
    urls = read_urls_from_csv(CSV_PATH)
    mvideos = []
    for url in urls:
        mvideos.append(MVideo(url))

    return mvideos