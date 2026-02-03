# Site Clipper

URL을 공유하면 웹 콘텐츠를 NotebookLM에 최적화된 마크다운(.md) 파일로 변환하는 앱.

단일 페이지 변환부터 사이트맵 기반 전체 문서 순회까지 지원하며, Android 공유 인텐트 또는 웹 프론트엔드를 통해 URL을 전달할 수 있다.

---

## 목차

- [빠른 시작](#빠른-시작)
- [아키텍처 개요](#아키텍처-개요)
- [프로젝트 구조](#프로젝트-구조)
- [Makefile 명령어](#makefile-명령어)
- [Backend 설정 및 실행](#backend-설정-및-실행)
- [Frontend 설정 및 실행](#frontend-설정-및-실행)
- [Android 설정 및 빌드](#android-설정-및-빌드)
- [API 명세](#api-명세)
- [코드 상세 설명](#코드-상세-설명)
- [환경 변수](#환경-변수)
- [Google Drive 연동 설정](#google-drive-연동-설정)
- [라이선스](#라이선스)

---

## 빠른 시작

### 사전 요구사항

- Python 3.11+
- Node.js 18+
- make (macOS/Linux 기본 포함)

### 설치 및 실행

```bash
# 1. 의존성 설치 (최초 1회)
make install

# 2. 개발 서버 실행 (backend + frontend 동시 실행)
make dev
```

실행 후 브라우저에서 **http://localhost:5173** 접속.

### 주요 명령어

| 명령어 | 설명 |
|--------|------|
| `make install` | 모든 의존성 설치 |
| `make dev` | Backend + Frontend 동시 실행 |
| `make dev-backend` | Backend만 실행 |
| `make dev-frontend` | Frontend만 실행 |
| `make build` | Frontend 프로덕션 빌드 |
| `make docker` | Docker로 Backend 실행 |
| `make help` | 모든 명령어 보기 |

---

## 아키텍처 개요

```
┌──────────────────┐
│  Web Frontend    │  HTTP
│  (React + Vite)  ├────────┐
└──────────────────┘        │
                            │    ┌─────────────────────────┐
┌──────────────────┐        ├───►│  FastAPI Backend         │
│  Android App     │  HTTP  │    │  (Python + Crawl4AI)     │
│  (Kotlin/Compose)├────────┘    │                           │
│                  │  SSE        │  Playwright (Headless)    │
│                  │◄────────────┤                           │
└──────────────────┘             └──────────┬──────────────┘
                                            │
                                  ┌─────────▼─────────┐
                                  │  Target Website    │
                                  │  (HTML → Markdown) │
                                  └────────────────────┘
```

### 동작 흐름

1. 사용자가 브라우저/앱에서 URL을 **공유(Share)** 하거나, 웹 프론트엔드에서 직접 입력한다.
2. 클라이언트(Android 앱 또는 웹 프론트엔드)가 URL을 백엔드 `POST /api/v1/crawl`로 전송한다.
3. 백엔드가 **Task ID**를 즉시 반환하고, 백그라운드에서 Crawl4AI로 페이지를 크롤링한다.
4. 앱은 **SSE**(Server-Sent Events)로 실시간 진행률을 수신한다. SSE 실패 시 폴링으로 전환한다.
5. 크롤링 완료 후 변환된 마크다운을 **로컬 저장**, **공유**, 또는 **Google Drive 업로드**한다.

---

## 프로젝트 구조

```
Site-Clipper/
├── frontend/                         # React 웹 프론트엔드
│   ├── package.json                  # npm 의존성
│   ├── vite.config.ts                # Vite 설정 (프록시 포함)
│   ├── index.html                    # HTML 엔트리포인트
│   └── src/
│       ├── main.tsx                  # React 앱 진입점
│       ├── App.tsx                   # 메인 컴포넌트
│       ├── App.module.css            # 스타일
│       └── api/
│           ├── types.ts              # TypeScript 타입 정의
│           └── client.ts             # API 클라이언트 + SSE
│
├── backend/                          # Python FastAPI 서버
│   ├── Dockerfile                    # Docker 이미지 빌드
│   ├── docker-compose.yml            # Docker Compose 설정
│   ├── requirements.txt              # Python 의존성
│   └── app/
│       ├── __init__.py
│       ├── main.py                   # FastAPI 앱 엔트리포인트
│       ├── core/
│       │   ├── config.py             # 환경 변수 기반 설정
│       │   └── crawler.py            # Crawl4AI 크롤링 엔진
│       ├── api/
│       │   ├── models.py             # Pydantic 요청/응답 모델
│       │   └── routes.py             # API 엔드포인트 (REST + SSE)
│       ├── services/
│       │   ├── markdown_service.py   # 마크다운 후처리 및 정제
│       │   ├── sitemap_service.py    # sitemap.xml 파싱
│       │   ├── task_service.py       # 작업 상태 관리 + 이벤트 알림
│       │   └── gdrive_service.py     # Google Drive 업로드
│       └── workers/
│           └── crawl_worker.py       # 백그라운드 크롤링 워커
│
├── android/                          # Android 앱 (Kotlin)
│   ├── build.gradle.kts              # 루트 Gradle 설정
│   ├── settings.gradle.kts           # 모듈 설정
│   ├── gradle.properties             # Gradle 프로퍼티
│   ├── gradle/wrapper/
│   │   └── gradle-wrapper.properties # Gradle 8.5 래퍼
│   └── app/
│       ├── build.gradle.kts          # 앱 모듈 빌드 설정
│       └── src/main/
│           ├── AndroidManifest.xml   # 인텐트 필터, 권한
│           ├── res/values/
│           │   ├── strings.xml       # 문자열 리소스
│           │   └── themes.xml        # 앱 테마
│           └── java/com/siteclipper/app/
│               ├── MainActivity.kt           # 앱 진입점
│               ├── data/
│               │   ├── ApiClient.kt          # Retrofit + OkHttp 설정
│               │   ├── ApiService.kt         # API 인터페이스 + 데이터 클래스
│               │   ├── ClipperRepository.kt  # 데이터 레이어
│               │   ├── FileManager.kt        # 로컬 파일 저장
│               │   ├── GoogleSignInHelper.kt # Google 로그인 헬퍼
│               │   ├── SseClient.kt          # SSE 클라이언트
│               │   └── UrlExtractor.kt       # URL 추출 정규식
│               └── ui/
│                   ├── ClipperViewModel.kt       # UI 상태 관리
│                   ├── CookieWebViewScreen.kt    # 쿠키 로그인 WebView
│                   └── ShareReceiverScreen.kt    # 메인 UI 화면
│
├── Makefile                          # 빌드/실행 자동화
├── PLAN.md                           # 개발 계획서
├── LICENSE                           # MIT 라이선스
└── README.md                         # 이 문서
```

---

## Makefile 명령어

프로젝트 루트에서 `make` 명령어로 빌드 및 실행을 자동화할 수 있다.

### 설치

```bash
# 모든 의존성 설치 (backend + frontend)
make install

# 개별 설치
make install-backend   # Python 의존성 + Playwright
make install-frontend  # npm 의존성
```

### 개발

```bash
# Backend + Frontend 동시 실행 (권장)
make dev

# 개별 실행
make dev-backend   # http://localhost:8000
make dev-frontend  # http://localhost:5173
```

### 빌드 및 배포

```bash
# Frontend 프로덕션 빌드
make build

# Docker로 Backend 실행
make docker
make docker-down  # 중지
```

### 유틸리티

```bash
make clean   # 빌드 캐시 정리
make health  # Backend 상태 확인
make help    # 모든 명령어 보기
```

---

## Backend 설정 및 실행

> **권장:** `make install-backend && make dev-backend` 사용

### 사전 요구사항

- Docker 및 Docker Compose **또는**
- Python 3.11+, pip

### Docker로 실행

```bash
make docker
# 또는
cd backend && docker compose up --build
```

서버가 `http://localhost:8000`에서 시작된다.

### 로컬 개발 환경에서 실행

```bash
# Makefile 사용 (권장)
make install-backend
make dev-backend
```

수동 설치:

```bash
cd backend

# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치 (Crawl4AI가 사용)
playwright install chromium

# 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 헬스 체크

```bash
curl http://localhost:8000/api/v1/health
# 응답: {"status":"ok"}
```

---

## Frontend 설정 및 실행

> **권장:** `make install-frontend && make dev-frontend` 사용
>
> 또는 Backend와 함께: `make install && make dev`

### 사전 요구사항

- Node.js 18+
- npm 또는 yarn

### 개발 서버 실행

```bash
# Makefile 사용 (권장)
make install-frontend
make dev-frontend

# Backend와 함께 실행
make dev  # backend + frontend 동시 실행
```

수동 설치:

```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

개발 서버는 `/api` 요청을 `http://localhost:8000`으로 프록시한다. 백엔드가 먼저 실행 중이어야 한다.

### 프로덕션 빌드

```bash
make build
# 또는
cd frontend && npm run build
```

빌드 결과물은 `frontend/dist/` 디렉터리에 생성된다.

### 사용 방법

1. 브라우저에서 `http://localhost:5173` 접속
2. URL 입력 후 "Convert" 클릭
3. 진행률 바를 통해 실시간 변환 상태 확인
4. 완료 후:
   - **Download .md**: 마크다운 파일 다운로드
   - **Raw/Rendered**: 원본 마크다운과 렌더링된 뷰 전환
   - **New URL**: 새 URL 변환 시작

---

## Android 설정 및 빌드

### 사전 요구사항

- Android Studio Hedgehog (2023.1.1) 이상
- JDK 17
- Android SDK 34

### 빌드 및 실행

1. Android Studio에서 `android/` 디렉터리를 연다.
2. Gradle Sync를 실행한다.
3. 에뮬레이터 또는 실제 디바이스에서 실행한다.

### 서버 주소 설정

기본값은 `http://10.0.2.2:8000` (에뮬레이터에서 호스트 머신의 localhost를 가리킴).

실제 디바이스에서 테스트할 때는 `android/app/build.gradle.kts`에서 변경한다:

```kotlin
buildConfigField("String", "API_BASE_URL", "\"http://서버_IP:8000\"")
```

### 사용 방법

1. **URL 공유**: 브라우저나 다른 앱에서 공유 버튼을 누르고 "Site Clipper"를 선택한다.
2. **변환 대기**: 진행률 바가 표시되며 마크다운 변환이 진행된다.
3. **결과 활용**:
   - **Save File**: `Documents/SiteClipper/` 폴더에 .md 파일 저장
   - **Share**: 다른 앱으로 마크다운 텍스트 공유
   - **Upload to Google Drive**: Google Drive의 SiteClipper 폴더에 업로드
4. **로그인 필요 사이트**: 에러 발생 시 "Login & Retry" 버튼으로 WebView에서 로그인 후 재시도

---

## API 명세

모든 엔드포인트의 prefix는 `/api/v1` 이다.

### `POST /api/v1/crawl`

URL 크롤링 작업을 생성한다.

**Request Body:**

```json
{
  "url": "https://example.com/docs/getting-started",
  "sitemap": false,
  "cookies": [
    {
      "name": "session_id",
      "value": "abc123",
      "domain": "example.com",
      "path": "/"
    }
  ]
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `url` | string | O | 크롤링 대상 URL |
| `sitemap` | boolean | X | `true`이면 sitemap.xml을 파싱하여 모든 하위 페이지를 순회 |
| `cookies` | array | X | 로그인이 필요한 사이트용 쿠키 목록 |

**Response:**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending"
}
```

---

### `GET /api/v1/tasks/{task_id}`

작업 상태 및 결과를 조회한다.

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "https://example.com/docs/getting-started",
  "status": "completed",
  "progress": 100,
  "total_pages": 1,
  "processed_pages": 1,
  "result": "---\ntitle: \"Getting Started\"\nsource: \"https://example.com/docs/getting-started\"\ndate: \"2026-02-01\"\n---\n\n# Getting Started\n...",
  "error": null
}
```

| `status` 값 | 설명 |
|------------|------|
| `pending` | 작업 대기 중 |
| `processing` | 크롤링 진행 중 |
| `completed` | 완료 (result 필드에 마크다운) |
| `failed` | 실패 (error 필드에 오류 메시지) |

---

### `GET /api/v1/tasks/{task_id}/stream`

SSE(Server-Sent Events)로 실시간 진행 상태를 스트리밍한다.

**이벤트 종류:**

| 이벤트 | 설명 | 데이터 예시 |
|--------|------|------------|
| `progress` | 진행률 업데이트 | `{"status":"processing","progress":45,"total_pages":10,"processed_pages":4}` |
| `done` | 작업 완료/실패 | `{"status":"completed","progress":100,"result":"...","error":null}` |
| `ping` | 연결 유지 (30초 간격) | 빈 문자열 |

**curl로 테스트:**

```bash
curl -N http://localhost:8000/api/v1/tasks/{task_id}/stream
```

---

### `POST /api/v1/drive/upload`

완료된 작업의 결과를 Google Drive에 업로드한다.

**Request Body:**

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "access_token": "ya29.a0Af...",
  "filename": "getting-started.md"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `task_id` | string | O | 완료된 크롤링 작업 ID |
| `access_token` | string | O | Google OAuth 액세스 토큰 |
| `filename` | string | X | 저장할 파일명 (미지정 시 URL 기반 자동 생성) |

**Response:**

```json
{
  "file_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2wtIs",
  "name": "getting-started.md",
  "web_link": "https://drive.google.com/file/d/1Bxi.../view"
}
```

---

### `GET /api/v1/health`

서버 상태 확인.

```json
{"status": "ok"}
```

---

## 코드 상세 설명

### Backend

#### `app/main.py` - 앱 엔트리포인트

FastAPI 앱을 생성하고 CORS 미들웨어를 설정한다. `lifespan` 컨텍스트 매니저에서 서버 시작 시 Crawl4AI의 Playwright 브라우저를 미리 워밍업하여 첫 번째 요청의 지연을 줄인다.

#### `app/core/config.py` - 설정 관리

`pydantic-settings`를 사용하여 환경 변수에서 설정을 읽는다. 모든 변수는 `CLIPPER_` 접두사를 사용한다. 상세 내용은 [환경 변수](#환경-변수) 섹션 참조.

#### `app/core/crawler.py` - 크롤링 엔진

Crawl4AI 라이브러리를 사용하여 URL을 마크다운으로 변환한다. 핵심은 **노이즈 제거**다:

- **제거 태그**: `nav`, `footer`, `header`, `aside`, `script`, `style`, `noscript`, `iframe`, `form`
- **제거 CSS 셀렉터**: sidebar, menu, cookie banner, popup, modal, 광고 관련 클래스/ID (총 23개 셀렉터)
- **옵션**: `word_count_threshold=10` (단어 10개 미만 블록 제거), `remove_forms=True`
- **쿠키 지원**: `BrowserConfig.cookies`를 통해 로그인 세션 쿠키를 Playwright 브라우저에 주입

Crawl4AI는 `fit_markdown`(정제된 버전)을 우선 반환하고, 없으면 `markdown`(원본)을 반환한다.

#### `app/api/models.py` - 데이터 모델

Pydantic BaseModel 기반으로 API 요청/응답을 정의한다:

- `TaskStatus` - 작업 상태 열거형 (pending, processing, completed, failed)
- `CookieItem` - 브라우저 쿠키 (name, value, domain, path)
- `CrawlRequest` - 크롤링 요청 (url, sitemap 여부, cookies)
- `TaskResult` - 작업 결과 (진행률, 페이지 수, 마크다운 결과)
- `DriveUploadRequest/Response` - Google Drive 업로드용

#### `app/api/routes.py` - API 라우터

5개의 엔드포인트를 정의한다:

1. `POST /crawl` - 크롤링 작업 생성. `BackgroundTasks`로 워커를 비동기 실행하고 즉시 task_id를 반환한다.
2. `GET /tasks/{id}` - 작업 상태 조회 (폴링용).
3. `GET /tasks/{id}/stream` - SSE 스트리밍. `task_store.subscribe()`로 이벤트를 구독하고, 상태 변경 시마다 클라이언트에 `progress` 이벤트를 전송한다. 작업 완료/실패 시 `done` 이벤트와 함께 스트림을 종료한다. 30초간 변경이 없으면 `ping`으로 연결을 유지한다.
4. `POST /drive/upload` - 완료된 작업의 마크다운을 Google Drive에 업로드한다.
5. `GET /health` - 헬스 체크.

#### `app/services/markdown_service.py` - 마크다운 후처리

크롤러가 반환한 원시 마크다운을 NotebookLM에 적합하게 정제한다:

- **YAML Front Matter 삽입**: 문서 상단에 title, source URL, 추출 날짜를 추가한다.
- **제목 추출**: 첫 번째 `# heading`을 제목으로 사용한다. 없으면 첫 줄을 사용한다.
- **노이즈 제거**:
  - 빈 링크 (`[](url)`, `[text]()`)
  - 아이콘 수준의 짧은 alt 텍스트를 가진 이미지
  - 네비게이션 화살표 기호만 있는 줄
  - "Skip to content", "Share", "Tweet" 등 UI 텍스트
  - 연속된 수평선 (`---`)
  - 3줄 이상의 연속 공백 줄

#### `app/services/sitemap_service.py` - 사이트맵 파서

대상 사이트의 `/sitemap.xml`을 가져와 모든 URL을 추출한다. sitemap index (중첩된 사이트맵)도 지원하여 하위 사이트맵을 재귀적으로 파싱한다. `httpx` 비동기 클라이언트를 사용하며 리다이렉트를 자동으로 따라간다.

#### `app/services/task_service.py` - 작업 상태 관리

인메모리 `TaskStore`에서 작업의 생명주기를 관리한다:

- `create()` - UUID 기반 task_id 생성
- `update_status()` - 상태 변경 + SSE 구독자에게 알림
- `update_progress()` - 진행률 업데이트 (processed/total 기반 퍼센트 계산)
- `set_result()` / `set_error()` - 최종 결과 저장
- `subscribe()` / `unsubscribe()` - `asyncio.Event` 기반 SSE 이벤트 구독. 상태가 변경될 때마다 `_notify()`가 모든 구독자의 Event를 set하여 SSE 제너레이터가 깨어나도록 한다.

#### `app/services/gdrive_service.py` - Google Drive 업로드

Google API Python 클라이언트를 사용하여 마크다운 파일을 업로드한다:

1. OAuth 액세스 토큰으로 Drive 서비스를 인증한다.
2. "SiteClipper" 폴더가 없으면 생성한다.
3. 마크다운 내용을 `text/markdown` MIME 타입으로 업로드한다.
4. file_id, 파일명, 웹 링크를 반환한다.

#### `app/workers/crawl_worker.py` - 백그라운드 크롤링 워커

`run_crawl_task()`가 실제 크롤링을 수행한다:

- **단일 페이지**: `crawl_url()` → `process_markdown()` → 결과 저장
- **사이트맵 모드**:
  1. `fetch_sitemap_urls()`로 모든 URL을 수집한다.
  2. `asyncio.Semaphore`로 동시 크롤링 수를 제한한다 (기본 10개).
  3. 배치 단위로 `asyncio.gather()`를 실행하고, 배치 완료마다 진행률을 업데이트한다.
  4. 개별 페이지 실패는 건너뛰고, 모든 페이지 실패 시에만 에러를 발생시킨다.
  5. 성공한 페이지들의 마크다운을 `---` 구분자로 병합한다.

---

### Android

#### `MainActivity.kt` - 앱 진입점

`ComponentActivity`를 상속하며 두 가지 방식으로 실행된다:

- **런처**: 앱을 직접 열면 Idle 상태의 안내 화면을 표시한다.
- **공유 인텐트**: 다른 앱에서 URL을 공유하면 `Intent.ACTION_SEND`로 실행된다. `UrlExtractor`로 텍스트에서 URL을 추출하여 `ShareReceiverScreen`에 전달한다.

`MaterialTheme`으로 Compose UI를 감싸 Material3 테마를 적용한다.

#### `data/UrlExtractor.kt` - URL 추출

정규식 `https?://[^\s<>"{}|\\^` + "`" + `\[\]]+`으로 공유된 텍스트에서 첫 번째 URL을 추출한다. 브라우저 공유 시 URL 외에 페이지 제목 등이 포함될 수 있으므로 정규식으로 URL만 분리한다.

#### `data/ApiClient.kt` - HTTP 클라이언트

Retrofit2 + OkHttp3 기반 HTTP 클라이언트. 설정:

- 연결 타임아웃: 30초
- 읽기 타임아웃: 60초 (크롤링 대기)
- 디버그 모드에서 HTTP 로깅 활성화
- `BuildConfig.API_BASE_URL`에서 서버 주소를 읽음

#### `data/ApiService.kt` - API 인터페이스

Retrofit 인터페이스로 백엔드 API를 정의한다. 데이터 클래스도 함께 선언:

- `CookieItem` - 쿠키 데이터
- `CrawlRequest/Response` - 크롤링 요청/응답
- `TaskResult` - 작업 결과 (progress, total_pages, processed_pages 포함)
- `DriveUploadRequest/Response` - Drive 업로드용

#### `data/ClipperRepository.kt` - Repository 패턴

API 호출을 추상화하는 데이터 레이어:

- `submitUrl()` - 크롤링 요청 전송 (쿠키 포함 가능)
- `streamTask()` - SSE Flow 반환
- `uploadToDrive()` - Google Drive 업로드 요청
- `pollUntilDone()` - SSE 실패 시 폴링 fallback. 2초 간격으로 작업 상태를 확인하며, `onProgress` 콜백으로 진행률을 전달한다.

#### `data/SseClient.kt` - SSE 클라이언트

OkHttp3의 `EventSource`를 Kotlin `Flow`로 래핑한다:

- `streamTask()` - `callbackFlow`로 SSE 이벤트를 Flow로 변환한다.
- `progress` 이벤트: 진행률 업데이트를 Flow에 emit한다.
- `done` 이벤트: 최종 결과를 emit하고 Flow를 닫는다.
- 연결 실패 시 Flow가 예외로 종료되어 ViewModel에서 폴링으로 전환한다.

#### `data/FileManager.kt` - 파일 저장

Android Scoped Storage (MediaStore API)를 사용하여 마크다운 파일을 저장한다:

- 저장 경로: `Documents/SiteClipper/`
- MIME 타입: `text/markdown`
- `ContentResolver`를 통해 파일을 생성하고 내용을 쓴다.

#### `data/GoogleSignInHelper.kt` - Google 로그인

Google Sign-In API를 설정한다:

- `drive.file` 스코프를 요청하여 앱이 생성한 파일에만 접근한다.
- `requestServerAuthCode()`로 서버에서 사용할 인증 코드를 요청한다.
- `getLastSignedInAccount()`로 이미 로그인된 계정을 확인한다.

#### `ui/ClipperViewModel.kt` - 상태 관리

`StateFlow` 기반으로 UI 상태를 관리한다:

```
Idle → Submitting → Processing(progress) → Completed / Error
```

- `submit()` - URL 제출 후 SSE 스트리밍을 시도한다. SSE 실패 시 폴링으로 fallback한다.
- `setCookies()` - WebView에서 추출한 쿠키를 저장하여 다음 요청에 포함한다.
- `saveToFile()` - 마크다운을 로컬에 저장한다. 파일명은 URL 기반으로 자동 생성한다.
- `uploadToDrive()` - Google OAuth 토큰으로 Drive에 업로드한다.

#### `ui/CookieWebViewScreen.kt` - 쿠키 로그인 화면

로그인이 필요한 사이트를 위한 WebView 화면:

1. 대상 URL을 WebView에 로드한다.
2. 사용자가 사이트에 직접 로그인한다.
3. "Done" 버튼을 누르면 `CookieManager`에서 현재 도메인의 쿠키를 추출한다.
4. 추출된 쿠키를 `CookieItem` 리스트로 변환하여 콜백으로 전달한다.
5. ViewModel에 쿠키가 설정된 상태로 크롤링을 재시도한다.

#### `ui/ShareReceiverScreen.kt` - 메인 UI 화면

Jetpack Compose로 구현된 메인 화면. 상태별 UI:

| 상태 | UI |
|------|-----|
| **Idle** | "Share a URL from any app to convert it to markdown." 안내 텍스트 |
| **Submitting** | `CircularProgressIndicator` + "Submitting..." |
| **Processing** | 진행률 > 0이면 `LinearProgressIndicator` + 퍼센트, 아니면 `CircularProgressIndicator` |
| **Completed** | "Save File", "Share", "Upload to Google Drive" 버튼. 저장/업로드 완료 시 확인 텍스트 |
| **Error** | 에러 메시지 + "Retry", "Login & Retry" 버튼 |

Google Drive 업로드 시 `ActivityResultContracts`로 Google Sign-In 결과를 수신한다.

---

## 환경 변수

백엔드 서버의 환경 변수. 모두 `CLIPPER_` 접두사를 사용한다.

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `CLIPPER_DEBUG` | `false` | 디버그 모드 활성화 |
| `CLIPPER_ALLOWED_ORIGINS` | `["*"]` | CORS 허용 오리진 목록 |
| `CLIPPER_CRAWL_TIMEOUT` | `60` | 크롤링 타임아웃 (초) |
| `CLIPPER_MAX_CONCURRENT_TASKS` | `10` | 사이트맵 크롤링 시 최대 동시 크롤 수 |

`docker-compose.yml`에서 설정 예시:

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CLIPPER_DEBUG=true
      - CLIPPER_CRAWL_TIMEOUT=120
      - CLIPPER_MAX_CONCURRENT_TASKS=5
```

---

## Google Drive 연동 설정

Google Drive 업로드 기능을 사용하려면 Google Cloud Console에서 OAuth 클라이언트를 설정해야 한다.

### 1. Google Cloud 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/)에서 새 프로젝트를 생성한다.
2. **APIs & Services > Library**에서 "Google Drive API"를 검색하여 활성화한다.

### 2. OAuth 동의 화면 설정

1. **APIs & Services > OAuth consent screen**으로 이동한다.
2. User Type: **External** 선택.
3. 앱 이름, 이메일 등을 입력한다.
4. Scopes에서 `https://www.googleapis.com/auth/drive.file`을 추가한다.

### 3. OAuth 클라이언트 ID 생성

1. **APIs & Services > Credentials**에서 "Create Credentials > OAuth client ID"를 선택한다.
2. Application type: **Android** 선택.
3. 패키지 이름: `com.siteclipper.app` 입력.
4. SHA-1 인증서 지문을 입력한다:
   ```bash
   # 디버그 키스토어의 SHA-1
   keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android
   ```
5. 생성된 **Client ID**를 복사한다.

### 4. Android 코드에 Client ID 적용

`android/app/src/main/java/com/siteclipper/app/ui/ShareReceiverScreen.kt`에서:

```kotlin
val intent = GoogleSignInHelper.getSignInIntent(
    context,
    serverClientId = "YOUR_CLIENT_ID.apps.googleusercontent.com"  // 여기에 입력
)
```

이 값을 `local.properties`나 `BuildConfig`로 관리하는 것을 권장한다.

---

## 라이선스

MIT License. [LICENSE](LICENSE) 파일 참조.
