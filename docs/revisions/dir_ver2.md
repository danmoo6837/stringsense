# 디렉터리 구조 Ver2

## 1. 목적

이 문서는 자동 기타 채보 시스템의 권장 디렉터리 구조와 각 디렉터리의 책임을 정의한다.

---

## 2. 권장 구조

```text
stringsense/
├─ backend/
│  ├─ api/
│  │  ├─ routes/
│  │  └─ schemas/
│  ├─ services/
│  │  ├─ separation_service.py
│  │  ├─ transcription_service.py
│  │  ├─ tab_service.py
│  │  └─ pipeline_service.py
│  ├─ audio/
│  │  ├─ preprocess.py
│  │  ├─ features.py
│  │  └─ postprocess.py
│  ├─ transcription/
│  │  ├─ onset.py
│  │  ├─ pitch.py
│  │  ├─ note_event.py
│  │  └─ quantize.py
│  ├─ tab/
│  │  ├─ fretboard.py
│  │  ├─ mapping.py
│  │  └─ render_tab.py
│  ├─ export/
│  │  ├─ midi_writer.py
│  │  ├─ musicxml_writer.py
│  │  └─ exporter.py
│  ├─ models/
│  │  ├─ separation/
│  │  └─ transcription/
│  ├─ config/
│  └─ main.py
├─ frontend/
│  ├─ templates/
│  ├─ static/
│  └─ app.py
├─ data/
│  ├─ raw/
│  ├─ processed/
│  ├─ samples/
│  └─ outputs/
├─ scripts/
│  ├─ run_separation.py
│  ├─ run_transcription.py
│  ├─ run_tab_generation.py
│  └─ run_pipeline.py
├─ tests/
│  ├─ audio/
│  ├─ transcription/
│  ├─ tab/
│  └─ integration/
├─ envs/
├─ docs/
└─ README.md
```

---

## 3. 디렉터리별 책임

### `backend/`

백엔드 애플리케이션 코드가 위치한다. 오디오 처리, 채보, 탭 생성, API 진입점을 포함한다.

### `backend/api/`

웹 요청을 받는 계층이다. 라우트와 요청/응답 스키마를 분리한다.

### `backend/services/`

파이프라인 단계들을 조합하는 서비스 계층이다. 실제 비즈니스 흐름 제어를 담당한다.

### `backend/audio/`

오디오 전처리와 특징 추출 등 기초 신호처리 로직을 둔다.

### `backend/transcription/`

onset, pitch, note event, quantization 등 채보 핵심 로직을 둔다.

### `backend/tab/`

기타 지판 정보와 줄/프렛 매핑, 탭 렌더링을 담당한다.

### `backend/export/`

MIDI, MusicXML, 텍스트 탭 등 결과 파일 생성 로직을 둔다. 기존 `output/`보다 역할이 더 명확하다.

### `backend/models/`

모델 체크포인트, 모델 래퍼, 관련 설정을 둔다.

### `frontend/`

사용자에게 업로드와 결과 확인 화면을 제공한다. 서버 템플릿 방식이면 최소 구조만 유지해도 된다.

### `data/raw/`

사용자가 업로드한 원본 파일을 저장한다.

### `data/processed/`

전처리된 내부 오디오 파일과 중간 산출물을 저장한다.

### `data/samples/`

개발과 데모용 샘플 오디오를 저장한다.

### `data/outputs/`

최종 결과물인 MIDI, 탭, MusicXML, 분리 음원을 저장한다.

### `scripts/`

단계별 실행 또는 실험용 스크립트를 둔다. 운영 코드보다는 개발/실험 진입점에 가깝다.

### `tests/`

단위 테스트와 통합 테스트를 둔다. 최소한 오디오 전처리, pitch 추정, 탭 매핑 테스트는 분리하는 편이 좋다.

### `docs/`

기획서, 기능 명세, 아키텍처 문서를 보관한다.

---

## 4. 실행 흐름과 파일 위치

일반적인 실행 흐름은 다음과 같다.

1. 사용자가 파일을 업로드한다.
2. 원본 파일은 `data/raw/`에 저장한다.
3. 전처리 결과는 `data/processed/`에 저장한다.
4. 분리 및 채보 결과는 `data/outputs/`에 저장한다.
5. 웹 또는 CLI가 결과 경로를 사용자에게 반환한다.

---

## 5. 기존 구조 대비 개선 포인트

- `output/`은 결과 파일 폴더처럼 보이므로 코드 디렉터리 이름은 `export/`가 더 명확하다.
- `bakend/`처럼 오타 가능성이 있는 이름은 `backend/`로 통일하는 편이 좋다.
- API 계층, 서비스 계층, 알고리즘 계층을 분리하면 유지보수가 쉬워진다.
- `tests/`와 `docs/`를 초기에 잡아두면 이후 확장 비용이 줄어든다.

---

## 6. 최소 운영 규칙

- 모델 파일과 소스 코드는 분리한다.
- 원본 데이터와 생성 결과물은 별도 디렉터리에 둔다.
- 스크립트는 실험용, 서비스는 운영용으로 역할을 나눈다.
- 문서에 적힌 파일명과 실제 산출물 파일명을 일치시킨다.
