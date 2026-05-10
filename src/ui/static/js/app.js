/**
 * Video Search UI - Main Application Logic
 *
 * Handles:
 *  - Image upload (click + drag-and-drop)
 *  - API call to /api/search
 *  - Rendering search results with top-5 videos
 */
(function () {
  "use strict";

  // ---- DOM Elements ----
  const uploadArea = document.getElementById("upload-area");
  const fileInput = document.getElementById("file-input");
  const btnBrowse = document.getElementById("btn-browse");
  const uploadPlaceholder = document.getElementById("upload-placeholder");
  const uploadPreview = document.getElementById("upload-preview");
  const previewImage = document.getElementById("preview-image");
  const previewName = document.getElementById("preview-name");
  const previewMeta = document.getElementById("preview-meta");
  const btnChange = document.getElementById("btn-change");
  const btnSearch = document.getElementById("btn-search");

  const uploadSection = document.getElementById("upload-section");
  const loadingSection = document.getElementById("loading-section");
  const resultsSection = document.getElementById("results-section");
  const errorSection = document.getElementById("error-section");
  const loadingDesc = document.getElementById("loading-desc");
  const resultsGrid = document.getElementById("results-grid");
  const resultsCount = document.getElementById("results-count");
  const resultsSubtitle = document.getElementById("results-subtitle");
  const errorMessage = document.getElementById("error-message");
  const btnRetry = document.getElementById("btn-retry");
  const btnSearchAgain = document.getElementById("btn-search-again");
  const statusDot = document.getElementById("status-dot");
  const statusText = document.getElementById("status-text");

  let selectedFile = null;

  // ---- Helpers ----
  function showSection(section) {
    [uploadSection, loadingSection, resultsSection, errorSection].forEach(
      (s) => (s.style.display = "none")
    );
    section.style.display = "block";
  }

  function formatBytes(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
  }

  function formatDuration(sec) {
    if (!sec) return "N/A";
    const m = Math.floor(sec / 60);
    const s = Math.round(sec % 60);
    return m > 0 ? `${m}m ${s}s` : `${s}s`;
  }

  function setStatus(text, type) {
    statusText.textContent = text;
    statusDot.style.background =
      type === "loading"
        ? "var(--warning)"
        : type === "error"
        ? "var(--danger)"
        : "var(--success)";
    statusDot.style.boxShadow = `0 0 8px ${
      type === "loading"
        ? "var(--warning)"
        : type === "error"
        ? "var(--danger)"
        : "var(--success)"
    }`;
  }

  // ---- File Selection ----
  function handleFileSelect(file) {
    if (!file || !file.type.startsWith("image/")) {
      alert("Vui lòng chọn file ảnh hợp lệ.");
      return;
    }
    if (file.size > 16 * 1024 * 1024) {
      alert("File quá lớn. Tối đa 16MB.");
      return;
    }
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = function (e) {
      previewImage.src = e.target.result;
      previewName.textContent = file.name;
      previewMeta.innerHTML = `<span>${formatBytes(file.size)}</span><span>${file.type}</span>`;
      uploadPlaceholder.style.display = "none";
      uploadPreview.style.display = "flex";
    };
    reader.readAsDataURL(file);
  }

  // Click to browse
  btnBrowse.addEventListener("click", (e) => {
    e.stopPropagation();
    fileInput.click();
  });
  uploadArea.addEventListener("click", () => {
    if (uploadPlaceholder.style.display !== "none") fileInput.click();
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) handleFileSelect(fileInput.files[0]);
  });

  // Drag and drop
  uploadArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadArea.classList.add("drag-over");
  });
  uploadArea.addEventListener("dragleave", () =>
    uploadArea.classList.remove("drag-over")
  );
  uploadArea.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadArea.classList.remove("drag-over");
    if (e.dataTransfer.files.length > 0) handleFileSelect(e.dataTransfer.files[0]);
  });

  // Change image
  btnChange.addEventListener("click", (e) => {
    e.stopPropagation();
    selectedFile = null;
    fileInput.value = "";
    uploadPlaceholder.style.display = "flex";
    uploadPreview.style.display = "none";
  });

  // ---- Loading Steps Animation ----
  function animateLoadingSteps() {
    const steps = [
      document.getElementById("step-1"),
      document.getElementById("step-2"),
      document.getElementById("step-3"),
    ];
    const messages = [
      "Trích xuất đặc trưng Histogram + HOG...",
      "So sánh cosine similarity với database...",
      "Xếp hạng và chọn top video...",
    ];
    let idx = 0;
    const interval = setInterval(() => {
      idx++;
      if (idx >= steps.length) {
        clearInterval(interval);
        return;
      }
      steps[idx - 1].classList.remove("active");
      steps[idx - 1].classList.add("done");
      steps[idx].classList.add("active");
      loadingDesc.textContent = messages[idx];
    }, 1200);
    return interval;
  }

  // ---- Search ----
  async function performSearch() {
    if (!selectedFile) return;
    showSection(loadingSection);
    setStatus("Đang tìm kiếm...", "loading");

    // Reset loading steps
    document.querySelectorAll(".step").forEach((s) => {
      s.classList.remove("active", "done");
    });
    document.getElementById("step-1").classList.add("active");
    loadingDesc.textContent = "Trích xuất đặc trưng Histogram + HOG...";
    const stepInterval = animateLoadingSteps();

    const formData = new FormData();
    formData.append("image", selectedFile);
    formData.append("top_k", "5");

    try {
      const resp = await fetch("/api/search", { method: "POST", body: formData });
      const data = await resp.json();
      clearInterval(stepInterval);

      if (!resp.ok || !data.success) {
        throw new Error(data.error || "Lỗi không xác định từ server.");
      }

      renderResults(data);
      showSection(resultsSection);
      setStatus("Hoàn tất", "ok");
    } catch (err) {
      clearInterval(stepInterval);
      errorMessage.textContent = err.message || "Không thể kết nối tới server.";
      showSection(errorSection);
      setStatus("Lỗi", "error");
    }
  }

  btnSearch.addEventListener("click", performSearch);

  // ---- Render Results ----
  function renderResults(data) {
    const results = data.results || [];
    resultsCount.textContent = `${results.length} video`;
    resultsSubtitle.textContent = `Ảnh truy vấn: ${data.query_info?.image_name || "N/A"} (${formatBytes(data.query_info?.image_size || 0)})`;

    resultsGrid.innerHTML = "";
    if (results.length === 0) {
      resultsGrid.innerHTML = `<div class="error-card"><div class="error-icon">🔍</div><h3>Không tìm thấy kết quả</h3><p style="color:var(--text-secondary)">Không có video nào trong database phù hợp.</p></div>`;
      return;
    }

    results.forEach((r) => {
      const simPercent = (r.similarity * 100).toFixed(2);
      const simClass =
        r.similarity >= 0.7
          ? "similarity-high"
          : r.similarity >= 0.4
          ? "similarity-medium"
          : "similarity-low";
      const simColor =
        r.similarity >= 0.7
          ? "var(--success)"
          : r.similarity >= 0.4
          ? "var(--warning)"
          : "var(--danger)";
      const rankClass =
        r.rank <= 3 ? `rank-${r.rank}` : "rank-default";

      const card = document.createElement("div");
      card.className = "result-card";
      card.innerHTML = `
        <div class="result-card-inner">
          <div class="rank-badge ${rankClass}">${r.rank}</div>
          <div class="result-info">
            <div class="result-name" title="${r.video_name || ""}">${r.video_name || "Video " + r.video_id.substring(0, 8)}</div>
            <div class="result-meta">
              ${r.species ? `<span class="result-meta-item">🏷️ ${r.species}</span>` : ""}
              <span class="result-meta-item">⏱️ ${formatDuration(r.duration_sec)}</span>
              <span class="result-meta-item">🎞️ ${r.frame_count || "?"} frames</span>
              <span class="result-meta-item">🔑 ${r.keyframe_count || "?"} keyframes</span>
              ${r.width && r.height ? `<span class="result-meta-item">📐 ${r.width}×${r.height}</span>` : ""}
            </div>
            <a href="${r.video_url}" target="_blank" rel="noopener" class="result-link">
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M4 1H2C1.4 1 1 1.4 1 2V10C1 10.6 1.4 11 2 11H10C10.6 11 11 10.6 11 10V8M7 1H11V5M11 1L5 7" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              Xem video
            </a>
          </div>
          <div class="similarity-section">
            <div class="similarity-value ${simClass}">${simPercent}%</div>
            <div class="similarity-label">Cosine Similarity</div>
            <div class="similarity-bar-bg">
              <div class="similarity-bar" style="width:0%;background:${simColor};" data-width="${simPercent}%"></div>
            </div>
          </div>
        </div>`;
      resultsGrid.appendChild(card);
    });

    // Animate similarity bars
    requestAnimationFrame(() => {
      document.querySelectorAll(".similarity-bar").forEach((bar) => {
        bar.style.width = bar.dataset.width;
      });
    });
  }

  // ---- Retry / Search Again ----
  btnRetry.addEventListener("click", () => {
    showSection(uploadSection);
    setStatus("Sẵn sàng", "ok");
  });
  btnSearchAgain.addEventListener("click", () => {
    selectedFile = null;
    fileInput.value = "";
    uploadPlaceholder.style.display = "flex";
    uploadPreview.style.display = "none";
    showSection(uploadSection);
    setStatus("Sẵn sàng", "ok");
  });
})();
