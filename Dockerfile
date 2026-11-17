FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    NUMBA_CACHE_DIR=/tmp/numba-cache
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libsndfile1 ffmpeg musescore3 poppler-utils \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt requirements-eval.txt ./
RUN pip install --no-cache-dir -r requirements-eval.txt
COPY backend/app ./backend/app
COPY backend/evaluate.py ./backend/evaluate.py
COPY frontend ./frontend
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
