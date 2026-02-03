개발자이자 아키텍트로서, URL 공유만으로 웹 콘텐츠를 NotebookLM용 마크다운(.md) 파일로 변환하는 **'Markdown Clipper'** 앱 개발 계획서를 작성해 드립니다.

이 프로젝트는 단일 페이지 추출을 넘어, 문서 사이트의 전체 계층을 순회하여 통합하는 것을 최종 목표로 합니다.

---

## 📋 Site Clipper 개발 계획서

### 1. 프로젝트 목표 (Objectives)

* **MVP 목표:** 안드로이드 '공유' 인텐트를 통해 받은 단일 URL을 마크다운으로 변환하여 로컬 저장.
* **고도화 목표:** 사이트맵(Sitemap) 분석 및 하위 페이지 재귀적(Recursive) 크롤링을 통한 통합 문서 생성.
* **사용성 목표:** NotebookLM 업로드에 최적화된 포맷(출처 표기, 노이즈 제거) 유지.

---

### 2. 기술 스택 (Tech Stack)

* **Frontend:** Android (Kotlin, Jetpack Compose)
* **Backend:** Python (FastAPI + Crawl4AI) — *성능 및 Playwright 의존성 해결을 위해 필수*
* **Infrastructure:** Docker (서버 배포용), Google Drive API (선택 사항)

---

### 3. 단계별 상세 업무 (Roadmap & Checklists)

#### 🟩 1단계: 안드로이드 기반 구축 (Foundation)

* [x] 안드로이드 프로젝트 생성 및 UI 구성 (Jetpack Compose)
* [x] `AndroidManifest.xml`에 URL 공유 수신을 위한 `Intent-filter` 등록
* [x] 공유받은 텍스트에서 정규식을 이용해 URL만 추출하는 유틸리티 구현
* [x] 백엔드 API와의 통신을 위한 `Retrofit2` 또는 `Ktor` 클라이언트 설정

#### 🟦 2단계: 크롤링 서버 구축 (Backend/Core)

* [x] FastAPI 기본 엔드포인트 구축
* [x] `Crawl4AI` 라이브러리 연동 및 동적 페이지(JS) 렌더링 설정
* [x] **핵심 로직:** 마크다운 변환 시 불필요한 태그(nav, footer, ads) 제거 필터 최적화
* [x] 사이트 전체 순회를 위한 `sitemap.xml` 파서 구현
* [x] 서버를 Docker 컨테이너화하여 배포 준비

#### 🟧 3단계: 파일 처리 및 NotebookLM 최적화

* [x] 추출된 텍스트 상단에 원본 URL 및 추출 날짜 헤더 삽입 로직
* [x] 안드로이드 Scoped Storage를 활용한 `.md` 파일 로컬 저장 기능
* [x] **고도화:** 여러 개의 하위 페이지를 하나의 `.md` 파일로 병합(Concatenation)하는 기능
* [x] 파일 생성 완료 후 즉시 공유(Share to...) 기능을 통해 다른 앱으로 전달

#### 🟪 4단계: 테스트 및 고도화 (Advanced)

* [x] 로그인이나 세션이 필요한 문서 사이트 대응 (Cookie 전달 로직)
* [x] 크롤링 진행 상황을 앱에서 실시간으로 볼 수 있는 `WebSocket` 또는 `SSE` 연결
* [x] 변환된 파일을 Google Drive 특정 폴더로 자동 업로드 (NotebookLM 연동 강화)

---

### 4. 아키텍처 제언 (Architectural Insight)

시스템 엔지니어 관점에서 볼 때, 이 앱의 핵심은 **'상태 관리'**입니다.
단순 페이지는 즉시 응답이 가능하지만, 문서 전체 순회는 시간이 걸리는 **비동기 작업(Long-running Task)**입니다.

1. 사용자가 URL 공유.
2. 서버는 `Task ID`를 즉시 반환하고 백그라운드에서 `Crawl4AI` 실행.
3. 앱은 `WorkManager`를 통해 진행률을 폴링(Polling)하거나 알림(Notification)으로 완료 보고.
4. 완료 시 사용자가 파일을 확인.

---

### 5. 다음 단계 제언

이 계획서대로 진행하신다면, 우선 **'단일 페이지 변환'**부터 성공시키는 것이 중요합니다.

**먼저 백엔드 서버에서 URL을 넣으면 마크다운을 뱉어주는 API 코드를 구체적으로 짜드릴까요? 아니면 안드로이드에서 공유 인텐트를 받는 부분부터 도와드릴까요?**
