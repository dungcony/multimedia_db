"""
Kiem tra du lieu histogram da luu trong Supabase:
1. Doc lai vector tu DB, so sanh voi vector tinh local
2. Test similarity search bang anh query tu public/test_queries/
3. Hien thi ket qua truc quan

Chay: python src/services/verify_histogram.py
"""
import numpy as np
from pathlib import Path
import os
from dotenv import load_dotenv

# Import cac ham pipeline tu module chung (giong notebook)
from histogram_utils import (
    TABLE_NAME,
    extract_histogram_vector,
    cosine_similarity,
    search_similar,
)


def main():
    load_dotenv()

    project_root = Path(__file__).resolve().parents[2]
    query_dir = project_root / "public" / "test_queries"
    keyframe_dir = project_root / "public" / "keyframes"

    # ======================================================
    # STEP 1: Ket noi Supabase va doc du lieu
    # ======================================================
    print("=" * 60)
    print("  STEP 1: Doc vector tu Supabase")
    print("=" * 60)

    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("[ERROR] Thieu SUPABASE_URL hoac SUPABASE_KEY trong .env")
        return

    supabase = create_client(url, key)
    response = supabase.table(TABLE_NAME).select("*").execute()
    db_rows = response.data

    print(f"  So dong trong bang '{TABLE_NAME}': {len(db_rows)}")
    if not db_rows:
        print("  [ERROR] Khong co du lieu! Chay notebook histo.ipynb truoc.")
        return

    for row in db_rows[:3]:
        vid = row.get("video_id", "?")
        ts = row.get("timestamp", "?")
        vec_len = len(row.get("feature_vector", []))
        print(f"    video_id={vid}, timestamp={ts}, vector_dim={vec_len}")

    # ======================================================
    # STEP 2: So sanh vector DB vs vector tinh lai local
    # ======================================================
    print()
    print("=" * 60)
    print("  STEP 2: So sanh vector DB vs Local")
    print("=" * 60)

    match_count = 0
    mismatch_count = 0
    skip_count = 0

    for row in db_rows:
        fp = row.get("frame_path", "")
        if not fp or not Path(fp).exists():
            skip_count += 1
            continue

        vec_db = np.array(row["feature_vector"], dtype=np.float64)
        vec_local = extract_histogram_vector(fp)

        cos_sim = cosine_similarity(vec_db, vec_local)
        max_diff = float(np.max(np.abs(vec_db - vec_local)))

        name = Path(fp).name
        if cos_sim > 0.9999 and max_diff < 1e-6:
            match_count += 1
        else:
            mismatch_count += 1
            print(f"  [MISMATCH] {name}: cosine={cos_sim:.6f}, max_diff={max_diff:.8f}")

    print(f"\n  Ket qua: {match_count} MATCH, {mismatch_count} MISMATCH, {skip_count} SKIP")
    if mismatch_count == 0 and match_count > 0:
        print("  >>> TAT CA VECTOR DA LUU CHINH XAC!")
    elif match_count == 0:
        print("  >>> Khong co vector nao kiem tra duoc (file khong ton tai).")
    else:
        print("  >>> CO SAI LECH — kiem tra lai pipeline hoac precision.")

    # ======================================================
    # STEP 3: Test similarity search voi anh query
    # ======================================================
    print()
    print("=" * 60)
    print("  STEP 3: Test Similarity Search")
    print("=" * 60)

    query_images = sorted(query_dir.glob("query_*.jpg"))
    if not query_images:
        print(f"  Khong tim thay anh query trong {query_dir}")
        print("  Chay: python src/services/generate_test_keyframes.py")
        return

    print(f"  Tim thay {len(query_images)} anh query\n")

    total_correct = 0
    total_queries = 0

    for qpath in query_images:
        species = qpath.stem.replace("query_", "")
        query_vec = extract_histogram_vector(str(qpath))
        results = search_similar(query_vec, db_rows, top_k=5)

        top1_vid = results[0]["video_id"]
        is_correct = species in top1_vid
        status = "PASS" if is_correct else "FAIL"
        if is_correct:
            total_correct += 1
        total_queries += 1

        print(f"  [{status}] Query: {qpath.name} (loai: {species})")
        for rank, r in enumerate(results, 1):
            vid = r["video_id"]
            sim = r["similarity"]
            match = " <-- SAME" if species in vid else ""
            print(f"       #{rank}  {vid:30s}  sim={sim:.4f}{match}")
        print()

    print("=" * 60)
    print(f"  Top-1 Accuracy: {total_correct}/{total_queries}")
    if total_correct == total_queries:
        print("  >>> TAT CA QUERY DEU DUNG! Histogram similarity hoat dong tot.")
    else:
        print("  >>> Mot so query sai — can dieu chinh bins hoac phuong phap.")
    print("=" * 60)


if __name__ == "__main__":
    main()
