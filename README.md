# 학식묵자 (Haksikmukja)

<img width="256" height="256" alt="Image" src="https://github.com/user-attachments/assets/f9e3cc8a-b0e0-4803-a0b7-d35126fc8223" />

> "오늘 학식 뭐 나오지?"

**학식묵자**는 학교 홈페이지의 식단 정보를 크롤링하여 메뉴를 2D 이미지로 시각화하여 보여주는 데스크톱 위젯 애플리케이션입니다.
FastAPI의 비동기 처리 성능과 Pydantic의 데이터 검증을 활용해 빠르고 안정적인 서비스를 제공합니다.

## 주요 기능 (Key Features)
* **다양한 학교 및 식당 지원**: KAIST, 서울대 등 다양한 학교의 학식 정보를 제공합니다. 업데이트를 통해 지원하는 학교와 식당을 확장할 수 있습니다.
* **자동 크롤링**: 백엔드 서버가 시작될 때, 자동으로 최신 식단 정보를 수집합니다.
* **메뉴 시각화**: 메뉴를 분석해 그날의 식단을 AI gen 이미지로 보여줍니다.
* **언어 설정**: 한국어 & 영어를 지원합니다.
* **테마 설정**: Dark, Light, Navy, Pink 테마를 지원합니다.

## 기술 스택 (Tech Stack)

### Frontend
* **Electron**: 데스크톱 애플리케이션 프레임워크
* **Node.js**: 런타임 환경
* **Vanilla JS**: UI 로직 구현
* **HTML** & **CSS**

### Backend
* **FastAPI**: 메인 웹 프레임워크
* **Python**: 백엔드 언어
* **PostgreSQL**: 메인 데이터베이스
* **Google Gemini**: OCR(광학 문자 인식)
* **pollinations.ai(flux model)**: 이미지 생성

---

## 폴더 구조 (Project Structure)

```bash
haksikmukja/
├── backend/                # 백엔드 서버 (FastAPI)
│   ├── app/
│   │   ├── api/            # API 라우터 (Endpoints)
│   │   ├── core/           # 설정 파일 (Config)
│   │   ├── db/             # DB 모델 및 세션 관리
│   │   ├── schemas/        # Pydantic 모델 (Request/Response)
│   │   ├── services/       # 비즈니스 로직 (크롤러, AI, DB작업)
│   │   └── main.py         # 앱 진입점 (Entry Point)
│   └── requirements.txt    # 의존성 목록
├── assets/                 # 프론트엔드 리소스 (CSS, Images, Icons)
├── main.js                 # 프론트엔드 로직
├── index.html              # 메인 페이지
├── school-setup.html       # 학교 설정 페이지
├── calendar.html           # 캘린더 페이지
├── settings.html           # 설정 페이지
└── viewer.html             # 3D 뷰어 페이지


```

---

## 실행 방법 (How to Run)

### 1. Clone the repository

```bash
git clone https://github.com/secret-joojoo/haksikmukja.git
cd haksikmukja

```

### 2. Backend Setup

파이썬 가상환경을 생성하고 패키지를 설치합니다.

```bash
cd backend
python -m venv venv
# Mac: source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

```

### 3. Environment Variables

`.env` 파일을 `backend/` 위치에 생성하고 필요한 키를 입력하세요.

```env
DATABASE_URL=YOUR_DATABASE_URL
GEMINI_API_KEY=YOUR_GEMINI_KEY
DISCORD_WEBHOOK_URL=YOUR_DISCORD_WEBHOOK_URL

```

### 4. Run Server

`backend/`에서 FastAPI 서버를 실행합니다.

```bash
uvicorn app.main:app --reload

```

서버가 실행되면 `http://localhost:8000/docs` 에서 API 문서를 확인할 수 있습니다.

### 5. Frontend

`haksikmukja/`에서 Electron을 실행합니다.

```bash
npm start

```

---

## 설치 경로

* [exe 파일 (Google Drive)](https://drive.google.com/file/d/1EXwVR3oOxhZVwGUfMprxhtyIyBn8esBJ/view?usp=sharing)

---

## Release Notes

### v1.0.1 (2026-02-12) - 리팩토링 및 보안 강화

**Security (보안)**
* `nodeIntegration: true` 제거 및 `contextIsolation: true` 적용.
* `remote` 모듈 의존성 제거.
* **Preload Script 도입:** 메인 프로세스와 렌더러 프로세스 간의 통신을 `window.electronAPI`로 격리.
* **CSP (Content Security Policy) 적용:** 모든 HTML 파일에 보안 메타 태그 추가.

**Refactoring (구조 개선)**
* **관심사의 분리 (SoC):** HTML 파일 내에 혼재되어 있던 JavaScript 로직을 `assets/js/` 폴더로 분리.
* **상수 및 데이터 모듈화:** 번역 데이터(i18n), 학교 정보, 메뉴 타입 등을 `constants.js`로 통합 관리.
* **렌더링 로직 개선:** 문자열 결합 방식에서 컴포넌트 단위 함수(`createMenuCard`) 활용 방식으로 변경.
* **아이콘 이미지 폴더 정리**: `assets/images/`, `assets/icons/`의 아이콘들을 `assets/icons/` 경로로 통일.

**Performance (성능)**
* **Resize Observer 최적화:** 윈도우 크기 조절 로직에 **Debouncing(디바운싱)** 기법을 적용하여 불필요한 IPC 통신 최소화.

**Fixes & Features (수정 및 기능)**
* **자동 실행:** 앱T 최초 실행 시 윈도우 시작 프로그램 등록 로직 추가.
* **UI 개선**: 학교 설정 창에서 검색된 학교 리스트에 따라 창 크기 변화.

---

## 아이콘 저작권
* <a href="https://www.flaticon.com/kr/free-icons/" title="학교 아이콘">학교 아이콘 제작자: Freepik - Flaticon</a>
* <a href="https://www.flaticon.com/kr/free-icons/" title="캘린더 아이콘">캘린더 아이콘 제작자: Abdul-Aziz - Flaticon</a>
* <a href="https://www.flaticon.com/kr/free-icons/" title="설정 아이콘">설정 아이콘 제작자: feen - Flaticon</a>
* <a href="https://www.flaticon.com/kr/free-icons/" title="쌀 아이콘">쌀 아이콘 제작자: Vectors Market - Flaticon</a>
