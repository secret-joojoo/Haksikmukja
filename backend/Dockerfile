# 1. 파이썬 3.11 버전이 깔린 리눅스를 기본으로 쓴다 (가볍고 빠름)
FROM python:3.11-slim

# 2. 작업할 폴더를 만든다
WORKDIR /app

# 3. 필요한 라이브러리 목록을 복사한다
COPY requirements.txt .

# 4. 라이브러리를 설치한다 (가상환경 필요 없음, 어차피 격리된 공간이라)
RUN pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드를 몽땅 복사한다
COPY . .

# 6. 서버를 실행한다 (외부 접속 가능하게 0.0.0.0 설정)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]