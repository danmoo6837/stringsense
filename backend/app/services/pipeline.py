from app.models.schemas import AnalysisResult
from app.services import preprocess, transcribe, tab_mapping, export_files, tab_pdf
from pathlib import Path
import json
from app.services import rhythm


def run(audio_path: str, job_id: str, output_dir: str, original_filename: str | None = None) -> AnalysisResult:
    """업로드된 오디오 파일에 대해 전체 채보 파이프라인을 실행한다."""

    # 1. 전처리
    audio, sr = preprocess.load(audio_path)

    # 2. onset + pitch 추출 → note events
    note_events = transcribe.extract_notes(audio, sr, audio_path)

    # 3. 줄/프렛 매핑 (DP)
    tab_events = tab_mapping.map(note_events)

    # 4. MIDI 및 탭 파일 생성
    export_files.to_midi(note_events, output_dir)
    tab_text = export_files.to_tab(tab_events, output_dir)
    rhythm_result = rhythm.analyze(audio, sr)
    Path(output_dir, "rhythm.json").write_text(json.dumps(rhythm_result, indent=2), encoding="utf-8")
    title = Path((original_filename or Path(audio_path).name).replace("\\", "/")).stem
    tab_pdf.to_pdf(tab_events, output_dir, rhythm_result, title=title)

    # 원본 파일명 추출 (job_id_ 접두사 제거)
    raw_filename = Path(audio_path).name

    return AnalysisResult(
        job_id=job_id,
        tab=tab_text,
        note_count=len(note_events),
        bpm=rhythm_result["bpm"],
        rhythm=rhythm_result,
        midi_url=f"/files/{job_id}/result.mid",
        tab_url=f"/files/{job_id}/result_tab.txt",
        pdf_url=f"/files/{job_id}/result_tab.pdf",
        musicxml_url=f"/files/{job_id}/result.musicxml",
        original_audio_url=f"/raw/{raw_filename}",
    )
