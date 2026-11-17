const API_BASE = window.location.pathname.startsWith("/ui/")
  ? window.location.origin
  : "http://localhost:8000";
const RESULT_STORAGE_KEY = "stringsense_result";

const fileInput = document.querySelector("#audio-file");
const selectedFileEl = document.querySelector("#selected-file");
const sampleButton = document.querySelector("#sample-button");
const startButton = document.querySelector("#start-button");

let selectedFile = null;

if (fileInput && selectedFileEl) {
  fileInput.addEventListener("change", () => {
    const file = fileInput.files && fileInput.files[0];
    if (!file) return;

    selectedFile = file;
    const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
    selectedFileEl.innerHTML = `
      <div>
        <strong>${escapeHtml(file.name)}</strong>
        <p>${sizeMb} MB · 업로드 준비 완료</p>
      </div>
      <span class="soft-pill">선택됨</span>
    `;
  });
}

if (sampleButton) {
  sampleButton.addEventListener("click", async () => {
    sampleButton.disabled = true;
    try {
      const response = await fetch("./samples/00_BN3-119-G_solo.wav");
      if (!response.ok) throw new Error("샘플 음원을 불러오지 못했습니다.");
      const blob = await response.blob();
      selectedFile = new File([blob], "00_BN3-119-G_solo.wav", { type: "audio/wav" });
      if (fileInput) fileInput.value = "";
      if (selectedFileEl) {
      selectedFileEl.innerHTML = `
        <div>
          <strong>00_BN3-119-G_solo.wav</strong>
          <p>${(selectedFile.size / (1024 * 1024)).toFixed(2)} MB · 업로드 준비 완료</p>
        </div>
        <span class="soft-pill">선택됨</span>
      `;
      }
    } catch (error) {
      alert(error.message);
    } finally {
      sampleButton.disabled = false;
    }
  });
}

if (startButton) {
  startButton.addEventListener("click", async () => {
    if (!selectedFile) {
      alert("파일을 먼저 선택해주세요.");
      return;
    }

    setLoading(true);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await fetch(`${API_BASE}/analyze`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "분석 중 오류가 발생했습니다.");
      }

      const result = await res.json();
      localStorage.setItem(RESULT_STORAGE_KEY, JSON.stringify(result));
      window.location.href = "./result.html";
    } catch (e) {
      setLoading(false);
      alert(e.message);
    }
  });
}

bindResultPage();
bindTabPage();
bindPdfPreview();

async function bindPdfPreview() {
  const preview = document.querySelector("[data-pdf-preview]");
  if (!preview) return;
  const status = document.querySelector("[data-pdf-status]");
  const result = readStoredResult();
  if (!result?.pdf_url) {
    status.textContent = "PDF가 없는 이전 결과입니다. 음원을 다시 분석하면 PDF가 생성됩니다.";
    return;
  }
  const url = absoluteApiUrl(result.pdf_url);
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error("PDF 파일을 불러오지 못했습니다. 음원을 다시 분석해 주세요.");
    const blobUrl = URL.createObjectURL(await response.blob());
    preview.classList.remove("hidden");
    preview.src = `${blobUrl}#zoom=page-width&view=FitH&navpanes=0`;
    const download = document.querySelector("[data-pdf-download]");
    download.href = blobUrl;
    download.download = "result_tab.pdf";
    download.classList.remove("hidden");
    const open = document.querySelector("[data-pdf-open]");
    open.href = url;
    open.classList.remove("hidden");
    status.textContent = "미리보기가 지원되지 않는 브라우저에서는 PDF를 다운로드해 확인하세요.";
    window.addEventListener("pagehide", () => URL.revokeObjectURL(blobUrl), { once: true });
  } catch (error) {
    status.textContent = error.message;
  }
}

function bindResultPage() {
  const resultContentEl = document.querySelector("#result-content");
  const missingResultEl = document.querySelector("#missing-result");
  const tabPreviewEl = document.querySelector("#tab-preview");
  const midiDownloadEl = document.querySelector("#midi-download");
  const tabDownloadEl = document.querySelector("#tab-download");
  const noteCountEl = document.querySelector("#note-count");
  const originalAudioEl = document.querySelector("#original-audio");
  const resultFilenameEl = document.querySelector("#result-filename");

  if (!resultContentEl && !tabPreviewEl && !midiDownloadEl) return;

  const result = readStoredResult();
  if (!result) {
    showMissingState(resultContentEl, missingResultEl);
    return;
  }

  if (tabPreviewEl) {
    tabPreviewEl.textContent = result.tab || "생성된 TAB이 없습니다.";
  }

  bindDownload(midiDownloadEl, result.midi_url, "result.mid");
  bindTextDownload(tabDownloadEl, result.tab, "result_tab.txt");

  if (noteCountEl) {
    noteCountEl.textContent = `${result.note_count ?? 0}개 음표 검출`;
  }

  if (originalAudioEl && result.original_audio_url) {
    originalAudioEl.src = absoluteApiUrl(result.original_audio_url);
  }

  if (resultFilenameEl) {
    resultFilenameEl.textContent = `job_id: ${result.job_id} · ${result.note_count ?? 0}개 음표 검출`;
  }
}

function bindTabPage() {
  const tabContentEl = document.querySelector("#tab-content");
  const missingTabEl = document.querySelector("#missing-tab");
  const tabFullEl = document.querySelector("#tab-full");
  const tabSummaryEl = document.querySelector("#tab-summary");
  const tabDownloadEls = [
    document.querySelector("#tab-download-detail"),
    document.querySelector("#tab-download-side"),
  ];

  if (!tabContentEl && !tabFullEl) return;

  const result = readStoredResult();
  if (!result) {
    showMissingState(tabContentEl, missingTabEl);
    return;
  }

  if (tabFullEl) {
    tabFullEl.textContent = result.tab || "생성된 TAB이 없습니다.";
  }

  if (tabSummaryEl) {
    tabSummaryEl.textContent = `job_id: ${result.job_id} · ${result.note_count ?? 0}개 음표 검출`;
  }

  tabDownloadEls.forEach((el) => bindTextDownload(el, result.tab, "result_tab.txt"));
}

function bindTextDownload(anchor, text, filename) {
  if (!anchor) return;

  if (!text) {
    bindDownload(anchor, "", filename);
    return;
  }

  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  anchor.href = URL.createObjectURL(blob);
  anchor.download = filename;
}

function bindDownload(anchor, url, filename) {
  if (!anchor) return;

  if (!url) {
    anchor.removeAttribute("href");
    anchor.setAttribute("aria-disabled", "true");
    anchor.classList.add("button--disabled");
    anchor.textContent = "파일 없음";
    return;
  }

  anchor.href = absoluteApiUrl(url);
  anchor.download = filename;
}

function readStoredResult() {
  const raw = localStorage.getItem(RESULT_STORAGE_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw);
  } catch {
    localStorage.removeItem(RESULT_STORAGE_KEY);
    return null;
  }
}

function showMissingState(contentEl, missingEl) {
  if (contentEl) contentEl.classList.add("hidden");
  if (missingEl) missingEl.classList.remove("hidden");
}

function absoluteApiUrl(path) {
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_BASE}${path}`;
}

function setLoading(on) {
  if (!startButton) return;
  if (on) {
    startButton.textContent = "분석 중...";
    startButton.disabled = true;
  } else {
    startButton.textContent = "분석 시작";
    startButton.disabled = false;
  }
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#039;",
  }[char]));
}
