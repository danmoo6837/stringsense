document.querySelectorAll("button").forEach((button) => {
  button.addEventListener("click", (event) => {
    event.preventDefault();
  });
});

const fileInput = document.querySelector("#audio-file");
const selectedFile = document.querySelector("#selected-file");
const sampleButton = document.querySelector("#sample-button");

if (fileInput && selectedFile) {
  fileInput.addEventListener("change", () => {
    const file = fileInput.files && fileInput.files[0];
    if (!file) return;

    const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
    selectedFile.innerHTML = `
      <div>
        <strong>${file.name}</strong>
        <p>${sizeMb} MB · 업로드 준비 완료</p>
      </div>
      <span class="soft-pill">선택됨</span>
    `;
  });
}

if (sampleButton && selectedFile) {
  sampleButton.addEventListener("click", () => {
    selectedFile.innerHTML = `
      <div>
        <strong>sample_acoustic_riff.wav</strong>
        <p>00:42 · 44.1kHz · mono</p>
      </div>
      <span class="soft-pill">샘플 선택됨</span>
    `;
  });
}
