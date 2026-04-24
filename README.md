# Stringsense

오디오 파일을 업로드하면 기타 연주를 분석해 MIDI와 기타 탭 초안을 생성하는 졸업작품 프로젝트입니다.

현재 저장소는 크게 `frontend`, `bakend`, `docs` 세 영역으로 구성되어 있습니다.  
프론트는 발표 및 시연용 웹 화면, 백엔드는 추후 분석 파이프라인을 연결할 코드 뼈대, 문서는 기획/계획/개선 기록을 보관합니다.

## 현재 구조

```text
stringsense/
├─ bakend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ models/
│  │  ├─ routers/
│  │  └─ servies/
│  └─ re.txt
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
├─ readme.md
└─ ubuntu.tar
```

## 폴더 설명

### `frontend/`

사용자가 실제로 보게 될 웹 화면 시안이 들어 있습니다.

- [index.html](/mnt/c/Users/dlehd/Documents/stringsense/frontend/index.html)
  - 새 분석 시작 화면
  - 파일 업로드, 샘플 불러오기, 분석 시작
- [processing.html](/mnt/c/Users/dlehd/Documents/stringsense/frontend/processing.html)
  - 분석 진행 중 화면
  - 처리 상태 안내
- [result.html](/mnt/c/Users/dlehd/Documents/stringsense/frontend/result.html)
  - 분석 결과 화면
  - 원본/분리 음원 재생, MIDI 다운로드, 탭 미리보기
- [tab.html](/mnt/c/Users/dlehd/Documents/stringsense/frontend/tab.html)
  - 탭 상세 보기 화면
  - 큰 탭 보기, 파일 저장
- [styles.css](/mnt/c/Users/dlehd/Documents/stringsense/frontend/styles.css)
  - 프론트 공통 스타일
- [app.js](/mnt/c/Users/dlehd/Documents/stringsense/frontend/app.js)
  - 업로드 화면의 간단한 상호작용 처리

### `bakend/`

백엔드 코드 뼈대가 들어 있습니다. 아직 본격 구현 전 단계입니다.

- [main.py](/mnt/c/Users/dlehd/Documents/stringsense/bakend/app/main.py)
  - 백엔드 진입점 예정 파일
- [models](/mnt/c/Users/dlehd/Documents/stringsense/bakend/app/models)
  - 데이터 모델 관련 디렉터리
- [routers](/mnt/c/Users/dlehd/Documents/stringsense/bakend/app/routers)
  - API 라우터 관련 디렉터리
- [servies](/mnt/c/Users/dlehd/Documents/stringsense/bakend/app/servies)
  - 서비스 로직 관련 디렉터리

주의:
- 현재 `bakend`, `servies`는 오타가 있는 상태입니다.
- 추후 `backend`, `services`로 정리하는 것이 좋습니다.

### `docs/`

프로젝트 문서를 역할별로 분리해 보관합니다.

- [docs/original](/mnt/c/Users/dlehd/Documents/stringsense/docs/original)
  - 초기 원본 문서
- [docs/revisions](/mnt/c/Users/dlehd/Documents/stringsense/docs/revisions)
  - 원본을 개선한 문서
- [docs/plans](/mnt/c/Users/dlehd/Documents/stringsense/docs/plans)
  - 졸업작품 계획서와 견본 자료
- [docs/logs](/mnt/c/Users/dlehd/Documents/stringsense/docs/logs)
  - 작업 기록
- [docs/ui](/mnt/c/Users/dlehd/Documents/stringsense/docs/ui)
  - UI 관련 문서
- [docs/README.md](/mnt/c/Users/dlehd/Documents/stringsense/docs/README.md)
  - 문서 폴더 인덱스

## 문서 정리 상태

### 원본 문서

- [framework.md](/mnt/c/Users/dlehd/Documents/stringsense/docs/original/framework.md)
- [funcional.md](/mnt/c/Users/dlehd/Documents/stringsense/docs/original/funcional.md)
- [dir.md](/mnt/c/Users/dlehd/Documents/stringsense/docs/original/dir.md)

### 개선 문서

- [framework_ver2.md](/mnt/c/Users/dlehd/Documents/stringsense/docs/revisions/framework_ver2.md)
- [functional_ver2.md](/mnt/c/Users/dlehd/Documents/stringsense/docs/revisions/functional_ver2.md)
- [dir_ver2.md](/mnt/c/Users/dlehd/Documents/stringsense/docs/revisions/dir_ver2.md)

### 계획서 문서

- [졸업작품계획서_견본.pdf](/mnt/c/Users/dlehd/Documents/stringsense/docs/plans/졸업작품계획서_견본.pdf)
- [졸업작품계획서_초안_ver1.md](/mnt/c/Users/dlehd/Documents/stringsense/docs/plans/졸업작품계획서_초안_ver1.md)

### 작업 기록

- [worklog_2026-04-02.md](/mnt/c/Users/dlehd/Documents/stringsense/docs/logs/worklog_2026-04-02.md)

## 프론트 실행 방법

프론트는 정적 HTML 기반이라 간단히 실행할 수 있습니다.

```bash
cd /mnt/c/Users/dlehd/Documents/stringsense/frontend
python3 -m http.server 8000
```

브라우저에서 아래 중 하나를 열면 됩니다.

- `http://localhost:8000/index.html`
- `http://localhost:8000/processing.html`
- `http://localhost:8000/result.html`
- `http://localhost:8000/tab.html`

## 현재 작업 상태

- 프론트: 사용자 중심 화면 시안 구현 완료
- 문서: 원본/개선본/계획서/로그 분리 완료
- 백엔드: 구조만 존재, 실제 분석 파이프라인 연결 전

## 다음 정리 추천
4. 프론트와 백엔드 연결 시 `/upload`, `/process`, `/result` 라우트 구조 정리