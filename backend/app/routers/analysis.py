import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from app.models.schemas import AnalysisResult
from app.services import pipeline

router = APIRouter()

DATA_DIR = Path(__file__).parent.parent.parent / "data"


@router.post("/analyze", response_model=AnalysisResult)
async def analyze(file: UploadFile = File(...)):
    filename = file.filename or ""
    if not filename.lower().endswith((".mp3", ".wav")):
        raise HTTPException(status_code=400, detail="mp3 또는 wav 파일만 지원합니다.")

    job_id = str(uuid.uuid4())[:8]

    raw_dir = DATA_DIR / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{job_id}_{filename}"

    with open(raw_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    output_dir = DATA_DIR / "outputs" / job_id
    output_dir.mkdir(parents=True, exist_ok=True)

    result = pipeline.run(str(raw_path), job_id, str(output_dir))
    return result


@router.get("/files/{job_id}/{filename}")
def download_file(job_id: str, filename: str):
    path = DATA_DIR / "outputs" / job_id / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    return FileResponse(str(path), filename=filename)


@router.get("/raw/{filename}")
def get_raw_file(filename: str):
    path = DATA_DIR / "raw" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    return FileResponse(str(path))
