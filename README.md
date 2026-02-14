# 학식묵자 (Haksikmukja)

<img width="256" height="256" alt="Image" src="https://github.com/user-attachments/assets/f9e3cc8a-b0e0-4803-a0b7-d35126fc8223" />

> "오늘 학식 뭐 나오지?"

**학식묵자**는 학교의 식단 정보를 크롤링하여 메뉴를 2D 이미지로 시각화하여 보여주는 데스크톱 위젯 애플리케이션입니다.

## 주요 기능 (Key Features)
* **다양한 학교 및 식당 지원**: KAIST, 서울대 등 다양한 학교의 학식 정보를 제공합니다. 업데이트를 통해 지원하는 학교와 식당을 확장할 수 있습니다.
* **자동 크롤링**: 백엔드 서버가 시작될 때, 자동으로 최신 식단 정보를 수집합니다.
* **메뉴 시각화**: 메뉴를 분석해 그날의 식단을 AI gen 이미지로 보여줍니다.
* **언어 설정**: 한국어 & 영어를 지원합니다.
* **테마 설정**: Dark, Light, Navy, Pink 테마를 지원합니다.

## 기술 스택 (Tech Stack)

### Frontend
- **Desktop Framework**: Electron (Node.js + Chromium)
- **Languages**: HTML5, CSS3, Vanilla JavaScript (ES6+)
- **HTTP Client**: Axios
- **Communication**: IPC (Inter-Process Communication) Main-Renderer Pattern

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Database**: SQLite (Async/aiosqlite), SQLAlchemy (ORM)
- **Migration**: Alembic
- **Scheduler**: APScheduler (AsyncIO)
- **Deployment**: Fly.io

---

## 폴더 구조 (Project Structure)

```bash
Haksikmukja/
├── backend/                # 백엔드 서버 (FastAPI)
│   ├── alembic/            # DB 마이그레이션 설정
│   ├── app/
│   │   ├── api/            # API 라우터 (Endpoints)
│   │   ├── core/           # 설정 파일 (Config)
│   │   ├── db/             # DB 모델 및 세션 관리
│   │   ├── schemas/        # Pydantic 모델 (Request/Response)
│   │   ├── services/       # 비즈니스 로직 (크롤러, AI, DB작업)
│   │   └── main.py         # 앱 진입점 (Entry Point)
│   ├── requirements.txt    # 의존성 목록
│   ├── alembic.ini         # Alembic 설정 파일
│   └── Dockerfile          # 배포용 도커 설정
├── assets/                 # 프론트엔드 리소스 (CSS, JS, Icons)
├── main.js                 # 프론트엔드 로직
├── preload.js              # 
├── index.html              # 메인 페이지
├── school-setup.html       # 학교 설정 페이지
├── calendar.html           # 캘린더 페이지
├── settings.html           # 설정 페이지
├── viewer.html             # 3D 뷰어 페이지
└── update.html             # 업데이트 알림 페이지
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

## Frontend Updates

-None

---

## Backend Updates

### v0.0.2

기존의 불안정했던 서버 구조를 대대적으로 리팩토링하여 안정성과 확장성을 확보했습니다.

- **성능 최적화**: DB 조회 시 발생하던 N+1 문제를 `Eager Loading`으로 해결하여 쿼리 속도를 비약적으로 향상시켰습니다.
- **비동기 스케줄러 도입**: 기존 `BackgroundScheduler`를 `AsyncIOScheduler`로 교체하여 FastAPI의 비동기 환경과 완벽하게 호환되도록 수정했습니다.
- **데이터베이스 마이그레이션**: `Alembic`을 도입하여 체계적인 스키마 관리(Version Control)가 가능해졌습니다.
- **경량화**: 불필요한 OCR 라이브러리(Tesseract, OpenCV 등)를 제거하여 Docker 이미지 크기와 리소스 점유율을 대폭 줄였습니다.

---

## 아이콘 저작권

* <a href="https://www.flaticon.com/kr/free-icons/" title="학교 아이콘">학교 아이콘 제작자: Freepik - Flaticon</a>
* <a href="https://www.flaticon.com/kr/free-icons/" title="캘린더 아이콘">캘린더 아이콘 제작자: Abdul-Aziz - Flaticon</a>
* <a href="https://www.flaticon.com/kr/free-icons/" title="설정 아이콘">설정 아이콘 제작자: feen - Flaticon</a>
* <a href="https://www.flaticon.com/kr/free-icons/" title="쌀 아이콘">쌀 아이콘 제작자: Vectors Market - Flaticon</a>

---

## 설치 경로

* [exe 파일 (Google Drive)](https://drive.google.com/file/d/19qYztyvriFPndjkue1G2yOGwE7kNah4p/view?usp=drive_link)