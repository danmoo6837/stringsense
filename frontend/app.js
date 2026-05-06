const API_BASE = "http://localhost:8000";

// ── index.html: 파일 업로드 및 분석 시작 ──────────────────────────────────
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
        <strong>${file.name}</strong>
        <p>${sizeMb} MB · 업로드 준비 완료</p>
      </div>
      <span class="soft-pill">선택됨</span>
    `;
  });
}

if (sampleButton) {
  sampleButton.addEventListener("click", () => {
    if (selectedFileEl) {
      selectedFileEl.innerHTML = `
        <div>
          <strong>샘플 파일은 직접 업로드해 주세요</strong>
          <p>mp3 또는 wav 파일을 선택하세요.</p>
        </div>
        <span class="soft-pill">안내</span>
      `;
    }
  });
}

if (startButton) {
  startButton.addEventListener("click", async () => {
    if (!selectedFile) {
      alert("파일을 먼저 선택해 주세요.");
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
      localStorage.setItem("stringsense_result", JSON.stringify(result));
      window.location.href = "./result.html";
    } catch (e) {
      setLoading(false);
      alert(e.message);
    }
  });
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

// ── result.html: 결과 표시 ────────────────────────────────────────────────
const tabPreviewEl = document.querySelector("#tab-preview");
const midiDownloadEl = document.querySelector("#midi-download");
const noteCountEl = document.querySelector("#note-count");
const originalAudioEl = document.querySelector("#original-audio");
const resultFilenameEl = document.querySelector("#result-filename");

if (tabPreviewEl || midiDownloadEl) {
  const raw = localStorage.getItem("stringsense_result");
  if (raw) {
    const result = JSON.parse(raw);

    if (tabPreviewEl) {
      tabPreviewEl.textContent = result.tab;
    }

    if (midiDownloadEl) {
      midiDownloadEl.href = `${API_BASE}${result.midi_url}`;
      midiDownloadEl.download = "result.mid";
    }

    if (noteCountEl) {
      noteCountEl.textContent = `${result.note_count}개`;
    }

    if (originalAudioEl) {
      originalAudioEl.src = `${API_BASE}${result.original_audio_url}`;
    }

    if (resultFilenameEl) {
      resultFilenameEl.textContent = `job_id: ${result.job_id} · ${result.note_count}개 음표 검출`;
    }
  }
}

// ── tab.html: 탭 상세 보기 ────────────────────────────────────────────────
const tabFullEl = document.querySelector("#tab-full");

if (tabFullEl) {
  const raw = localStorage.getItem("stringsense_result");
  if (raw) {
    const result = JSON.parse(raw);
    tabFullEl.textContent = result.tab;
  }
}
