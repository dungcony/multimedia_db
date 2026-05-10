"""Flask API server cho hệ thống truy vấn video bằng ảnh.

Endpoints:
  POST /api/search  - Upload ảnh và tìm top-5 video tương đồng
  GET  /            - Giao diện web
  GET  /health      - Health check
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import cv2
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Thêm thư mục cha vào sys.path để import modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.search import search_similar_videos

app = Flask(
    __name__,
    static_folder=str(PROJECT_ROOT / "src" / "ui" / "static"),
    static_url_path="/static",
)
CORS(app)

# Giới hạn upload 16MB
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "webp", "tiff"}


def _allowed_file(filename: str) -> bool:
    """Kiểm tra file có đuôi hợp lệ."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    """Phục vụ trang chủ."""
    return send_from_directory(str(PROJECT_ROOT / "src" / "ui"), "index.html")


@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "Server đang hoạt động"})


@app.route("/api/search", methods=["POST"])
def search():
    """Tìm kiếm video tương đồng từ ảnh upload.

    Request:
        multipart/form-data với field 'image' chứa file ảnh.
        Optional: 'top_k' (int) - số lượng kết quả (mặc định 5).

    Response:
        JSON với danh sách video tương đồng.
    """
    # Validate input
    if "image" not in request.files:
        return jsonify({
            "success": False,
            "error": "Không tìm thấy file ảnh. Vui lòng upload ảnh.",
        }), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({
            "success": False,
            "error": "Tên file trống. Vui lòng chọn file ảnh.",
        }), 400

    if not _allowed_file(file.filename):
        return jsonify({
            "success": False,
            "error": f"Định dạng không hỗ trợ. Chấp nhận: {', '.join(ALLOWED_EXTENSIONS)}",
        }), 400

    top_k = request.form.get("top_k", 5, type=int)
    top_k = max(1, min(top_k, 20))  # Clamp 1-20

    try:
        # Đọc file ảnh từ request thành numpy array
        file_bytes = file.read()
        np_arr = np.frombuffer(file_bytes, np.uint8)
        image_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if image_bgr is None:
            return jsonify({
                "success": False,
                "error": "Không thể decode ảnh. File có thể bị hỏng.",
            }), 400

        # Tìm kiếm video tương đồng
        results = search_similar_videos(image_bgr, top_k)

        return jsonify({
            "success": True,
            "query_info": {
                "image_name": file.filename,
                "image_size": len(file_bytes),
                "image_shape": list(image_bgr.shape),
            },
            "total_results": len(results),
            "results": results,
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Lỗi xử lý: {str(e)}",
        }), 500


if __name__ == "__main__":
    print("=" * 60)
    print("  [*] Multimedia Database - Video Search System")
    print("  [>] http://localhost:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
