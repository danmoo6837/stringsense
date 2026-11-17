# Stringsense

오디오 파일을 업로드하면 기타 연주를 분석해 MIDI 파일과 기타 TAB 초안을 생성하는 졸업작품 프로젝트입니다.

현재 저장소는 FastAPI 백엔드, 정적 프론트엔드, 프로젝트 문서로 구성되어 있습니다.

## 구조

```text
stringsense/
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ models/
│  │  ├─ routers/
│  │  └─ services/
│  └─ data/              # 실행 중 생성되는 업로드/결과 파일
├─ frontend/
│  ├─ index.html
│  ├─ processing.html
│  ├─ result.html
│  ├─ tab.html
│  ├─ styles.css
│  └─ app.js
├─ docs/
│  ├─ original/
│  ├─ revisions/
│  ├─ plans/
│  ├─ logs/
│  ├─ ui/
│  └─ README.md
├─ requirements.txt
└─ README.md
```

## 백엔드

백엔드는 FastAPI 기반입니다.

- `backend/app/main.py`
  - FastAPI 앱 생성
  - CORS 설정
  - `/ui` 경로로 프론트엔드 정적 파일 제공
  - `/` 요청을 `/ui/index.html`로 리다이렉트
- `backend/app/routers/analysis.py`
  - `POST /analyze`: mp3/wav 업로드 후 분석 실행
  - `GET /files/{job_id}/{filename}`: 생성된 결과 파일 다운로드
  - `GET /raw/{filename}`: 업로드 원본 오디오 재생/다운로드
- `backend/app/services/`
  - `preprocess.py`: 오디오 로드와 정규화
  - `transcribe.py`: onset/pitch 기반 note event 추출
  - `tab_mapping.py`: 기타 줄/프렛 위치 매핑
  - `export_files.py`: MIDI와 TAB 텍스트 생성
  - `pipeline.py`: 전체 분석 흐름 조합

## 프론트엔드

프론트엔드는 별도 빌드 과정 없는 정적 HTML/CSS/JS입니다.

- `frontend/index.html`: 파일 업로드와 분석 시작 화면
- `frontend/processing.html`: 처리 상태 화면
- `frontend/result.html`: 분석 결과, 원본 오디오, MIDI 다운로드, TAB 미리보기
- `frontend/tab.html`: TAB 상세 보기
- `frontend/app.js`: `/analyze` 호출과 결과 화면 바인딩

## 실행

의존성 설치:

```bash
pip install -r requirements.txt
```

전사는 Basic Pitch를 우선 사용하고 실행 실패 또는 빈 결과일 때 librosa의 onset/pYIN/CQT 분석으로 대체합니다. 대체 경로에는 최근 librosa 개선을 유지했습니다. 기존 평가 보고서의 69.90%는 librosa 단독 버전의 점수이며 이 복원 버전의 점수가 아닙니다. Python 3.11 환경을 권장하며, conda를 사용한다면 다음처럼 실행합니다.

```bash
conda activate stringsense311
python -m uvicorn app.main:app --reload --app-dir backend
```

FastAPI 서버 실행:

```bash
uvicorn app.main:app --reload --app-dir backend
```

브라우저에서 접속:

```text
http://localhost:8000/
```

프론트엔드만 정적으로 확인하려면 다음처럼 실행할 수 있습니다.

```bash
cd frontend
python -m http.server 8000
```

다만 실제 분석 기능은 FastAPI 서버의 `/analyze` API가 실행 중이어야 동작합니다.

## API 흐름

1. 사용자가 `index.html`에서 mp3 또는 wav 파일을 선택합니다.
2. `frontend/app.js`가 `POST /analyze`로 파일을 업로드합니다.
3. 백엔드는 파일을 `backend/data/raw/`에 저장하고 분석 파이프라인을 실행합니다.
4. 결과 MIDI와 TAB 파일은 `backend/data/outputs/{job_id}/`에 생성됩니다.
5. 프론트엔드는 응답을 `localStorage`에 저장하고 `result.html`에서 표시합니다.

## 개발 메모

### 성능 평가

Docker에서 백엔드와 평가기를 실행하려면:

```bash
docker compose up -d --build backend
docker compose --profile evaluation run --rm evaluate
```

음원은 `backend/data/inputs/audio_mono-mic/solo/`와 `comp/`에 각각 관리합니다. 평가기는 하위 폴더까지 탐색합니다. solo만 평가하려면:

```bash
docker compose --profile evaluation run --rm evaluate python backend/evaluate.py --base-url http://backend:8000 --group solo
```

웹 화면은 `http://localhost:8001/ui/index.html`에서 확인합니다. 입력 데이터는 읽기 전용으로 마운트하고, 결과는 호스트의 `backend/data/evaluations/`에 저장합니다. 기존 Windows 서버와 별개로 실행되며, 종료는 `docker compose down`입니다. 첫 실행에서는 Numba 컴파일 때문에 시간이 더 걸릴 수 있습니다.

백엔드를 실행한 후 별도 터미널에서 다음을 실행합니다. 평가기는 실제 `/analyze` API에 WAV를 업로드하고, 응답의 MIDI를 다운로드해서 JAMS 정답과 비교합니다.

```bash
python -m pip install -r requirements-eval.txt
python backend/evaluate.py --validate-only
python backend/evaluate.py --limit 1
python backend/evaluate.py
```

- 기본 서버: `http://127.0.0.1:8000` (`--base-url`로 변경).
- 입력: `backend/data/inputs/annotation/*.jams`, `audio_mono-mic/*_mic.wav`.
- 출력: `backend/data/evaluations/<실행시각>/`의 `summary.json`, `tracks.csv`, 곡별 정답/검출 JSON 및 실제 다운로드 MIDI.
- 시작 ±50ms, 음높이 ±50센트로 일대일 매칭합니다. 종료 오차도 비교하는 별도 점수는 정답 길이의 20% 또는 50ms 중 큰 값을 허용합니다.
- 점수 범위는 0~1입니다. 전체 음표를 합산한 micro 점수와 곡별 F1 평균인 macro 점수, solo/comp별 결과를 제공합니다.
- `--limit`은 이름순 일부 곡만 평가하므로 전체 성능으로 보고하면 안 됩니다. 실패한 곡은 `errors`에 기록하며 성공한 곡만 집계합니다.
- 서버 엔진/버전은 API가 반환하지 않으므로 평가기가 추정하지 않습니다. 변경된 librosa 전사를 평가하려면 서버를 재시작하세요. 평가는 백엔드의 업로드·결과 파일도 생성합니다.
- 현재 백엔드 분석은 최대 60초로 제한됩니다. 더 긴 음원은 잘린 결과를 전체 정답과 비교하므로 누락 음으로 반영됩니다. 임시 PDF 템포는 평가에 사용하지 않습니다.

- 분석 시 `result_tab.pdf`도 생성됩니다. 결과/TAB 상세 화면에서 미리보기와 다운로드를 제공합니다.
- PDF는 `result.musicxml`을 만든 뒤 MuseScore로 조판합니다. 기타 관례에 따라 실제 소리보다 한 옥타브 높게 높은음자리 오선보에 표시하고 아래에 6줄 TAB을 배치하며 한 줄은 두 마디입니다.
- 오디오에서 BPM과 박 위치를 추정하고, 음 시작·종료를 16분음표 단위에 맞춥니다. 쉼표·화음·붙임줄을 기록합니다. 4/4와 첫 강박은 여전히 가정하며, 셋잇단음표·스윙은 해석하지 않습니다. 이 변환은 PDF에만 적용하며 평가용 MIDI의 음 시각은 바꾸지 않습니다.
- `docker compose up -d --build backend`로 MuseScore가 포함된 백엔드를 실행합니다. 직접 실행할 경우 MuseScore 설치 후 `MUSESCORE_BIN`에 실행 파일 경로를 지정합니다. `pip install`만으로는 조판 엔진이 설치되지 않습니다. 기존 결과는 재분석해야 새 PDF가 생깁니다.
- API의 `musicxml_url`로 편집 가능한 MusicXML도 내려받을 수 있습니다. MusicXML 단위 테스트: `backend`에서 `python -m unittest discover -s tests -p test_tab_pdf.py`.

- `backend/data/`, `__pycache__/`, 가상환경 폴더 등 실행 생성물은 git 추적 대상에서 제외합니다.
- 업로드 파일은 원본 파일명을 경로에 직접 사용하지 않고 서버가 생성한 `job_id` 기반 이름으로 저장합니다.
- Python 실행 환경이 준비되어 있어야 백엔드 실행과 분석 라이브러리 동작을 확인할 수 있습니다.
