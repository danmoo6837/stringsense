from pydantic import BaseModel


class AnalysisResult(BaseModel):
    job_id: str
    tab: str
    note_count: int
    midi_url: str
    tab_url: str
    pdf_url: str
    original_audio_url: str
    bpm: float = 120.0
    rhythm: dict | None = None
    musicxml_url: str | None = None
