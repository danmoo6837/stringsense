from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path

from app.routers import analysis

app = FastAPI(title="Stringsense API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router)

FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"
app.mount("/ui", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


@app.get("/")
def root():
    return RedirectResponse(url="/ui/index.html")
