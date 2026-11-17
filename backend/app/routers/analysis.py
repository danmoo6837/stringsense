import uuid
import shutil
import re
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from app.models.schemas import AnalysisResult
from app.services import pipeline

router = APIRouter()

DATA_DIR = Path(__file__).parent.parent.parent / "data"
SUPPORTED_AUDIO_SUFFIXES = {".mp3", ".wav"}
SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
JOB_ID_RE = re.compile(r"^[a-f0-9]{8}$")


@router.post("/analyze", response_model=AnalysisResult)
async def analyze(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_AUDIO_SUFFIXES:
        raise HTTPException(status_code=400, detail="mp3 또는 wav 파일만 지원합니다.")

    job_id = str(uuid.uuid4())[:8]

    raw_dir = DATA_DIR / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{job_id}{suffix}"

    with open(raw_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    output_dir = DATA_DIR / "outputs" / job_id
    output_dir.mkdir(parents=True, exist_ok=True)

    result = pipeline.run(str(raw_path), job_id, str(output_dir), original_filename=file.filename)
    return result


@router.get("/files/{job_id}/{filename}")
def download_file(job_id: str, filename: str, download: bool = False):
    _validate_job_id(job_id)
    _validate_filename(filename)
    path = DATA_DIR / "outputs" / job_id / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    if filename == "result_tab.pdf":
        return FileResponse(
            str(path), media_type="application/pdf", filename=filename,
            content_disposition_type="attachment" if download else "inline",
            headers={"Cache-Control": "no-store"},
        )
    return FileResponse(str(path), filename=filename)


@router.get("/raw/{filename}")
def get_raw_file(filename: str):
    _validate_filename(filename)
    path = DATA_DIR / "raw" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    return FileResponse(str(path))


def _validate_job_id(job_id: str) -> None:
    if not JOB_ID_RE.fullmatch(job_id):
        raise HTTPException(status_code=400, detail="잘못된 작업 ID입니다.")


def _validate_filename(filename: str) -> None:
    if Path(filename).name != filename or not SAFE_FILENAME_RE.fullmatch(filename):
        raise HTTPException(status_code=400, detail="잘못된 파일 이름입니다.")
