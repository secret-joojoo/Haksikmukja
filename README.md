# 학식묵자 (Haksikmukja)

<img width="256" height="256" alt="Image" src="https://github.com/user-attachments/assets/5109ddba-7715-4528-a6db-1f544421fa2c" />

> "오늘 학식 뭐 나오지?"

**학식묵자**는 학교의 식단 정보를 크롤링하여 메뉴를 2D 이미지로 시각화하여 보여주는 데스크톱 위젯 애플리케이션입니다.

## 주요 기능 (Key Features)
* **다양한 학교 및 식당 지원**: KAIST, 서울시립대학교 등 다양한 학교의 학식 정보를 제공합니다. 업데이트를 통해 학교와 식당을 확장할 수 있습니다.
* **자동 크롤링**: 매일 00:01에 자동으로 최신 식단 정보를 수집합니다.
* **메뉴 시각화**: 메뉴를 분석하여 그날의 식단을 AI gen 이미지로 보여줍니다.

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
├── preload.js              # Main-Renderer 간 IPC 통신 브리지
├── index.html              # 메인 페이지
├── school-setup.html       # 학교 설정 페이지
├── calendar.html           # 캘린더 페이지
├── settings.html           # 설정 페이지
├── viewer.html             # 3D 뷰어 페이지
└── update.html             # 업데이트 알림 페이지
```

---

## Frontend Updates

### v1.0.2

- **KAIST 식당 업데이트**: 동맛골 제거 & 문지캠퍼스 및 화암 기숙사식당 추가
- **서울시립대학교 추가**: 학생회관 1층, 이룸라운지, 양식당, 자연과학관 추가

### v1.0.3

- **KAIST 서맛골 개선**: 석식 일품이 '석식 일품', 'DINNER SPECIAL'로 표기되도록 개선.
- **서울시립대학교 이룸라운지 개선**: '플러스 메뉴'를 파싱하도록 개선.
- **서울시립대학교 양식당 개선**: 메뉴명과 가격이 혼재된 텍스트에서 '메뉴명: 가격' 형태로 깔끔하게 매핑.

---

## Backend Updates

### v0.0.2 (Release: v1.0.1)

- **성능 최적화**: DB 조회 시 발생하던 N+1 문제를 `Eager Loading`으로 해결하여 쿼리 속도 향상.
- **비동기 스케줄러 도입**: 기존 `BackgroundScheduler`를 `AsyncIOScheduler`로 교체하여 FastAPI의 비동기 환경과 완벽하게 호환되도록 수정.
- **데이터베이스 마이그레이션**: `Alembic`을 도입하여 체계적인 스키마 관리(Version Control).
- **경량화**: 불필요한 OCR 라이브러리를 제거.

### v0.0.3 (Release: v1.0.2)

- **크롤러 아키텍처 리팩토링**: 기존 단일 스크래퍼 방식에서 식당별 개별 Parser 모듈화 구조로 변경 (확장성 및 유지보수성 강화).
- **학교 및 식당 업데이트**: KAIST, 서울시립대학교 크롤링 로직 추가.
- **자동 데이터 관리 기능 탑재**: 서버 시작 시 init_data.py가 실행되어 학교 및 식당 기초 데이터가 없으면 자동으로 생성.
- **Garbage Collection**: 매일 새벽 00:31, 3일 이상 지난 메뉴 데이터를 자동 삭제하도록 스케줄러 등록.
- **시간대 조정**: 서버 타임존을 Asia/Seoul로 명시하여 크롤링 스케줄 정확도 향상.

### v0.0.4 (Release: v1.0.3)

- **서울시립대학교 크롤링 로직 개편**: 기존 GET 방식에서 날짜 데이터가 갱신되지 않던 문제를 해결하기 위해 `httpx`를 사용한 POST 요청으로 변경.
- **DB 서비스 로직 수정**: 오래된 메뉴 삭제(`delete_old_menus`) 기능 실행 시 발생하던 `datetime` 모듈 누락 에러를 수정.
- **문의 알림 개선**: 디스코드 채널로 전송되는 알림 메시지의 가독성 향상.
- **의존성 정리**: `requirements.txt` 내 중복 패키지(`google-generativeai`) 제거 및 배포 환경 최적화.

### v0.0.5 (Release: v1.0.3)

- **스케줄러(APScheduler) 실행 안정성 강화**: 크롤링 및 DB 청소 작업의 `misfire_grace_time`을 60초로 설정하여 미세한 서버 딜레이가 발생하더라도 작업이 무시되지 않고 안정적으로 백그라운드 크롤링이 수행되도록 개선.

---

## 설치

* [exe 파일 (Google Drive)](https://drive.google.com/file/d/1FpfIuGwwcKIE-po7YXzldy1HCL2OXdT_/view?usp=sharing)

---

## 아이콘 저작권

* <a href="https://www.flaticon.com/kr/free-icons/" title="학교 아이콘">학교 아이콘 제작자: Freepik - Flaticon</a>
* <a href="https://www.flaticon.com/kr/free-icons/" title="캘린더 아이콘">캘린더 아이콘 제작자: Abdul-Aziz - Flaticon</a>
* <a href="https://www.flaticon.com/kr/free-icons/" title="설정 아이콘">설정 아이콘 제작자: feen - Flaticon</a>
* <a href="https://www.flaticon.com/kr/free-icons/" title="쌀 아이콘">쌀 아이콘 제작자: Vectors Market - Flaticon</a>