from pydantic import BaseModel


class AnalysisResult(BaseModel):
    job_id: str
    tab: str
    note_count: int
    midi_url: str
    original_audio_url: str
