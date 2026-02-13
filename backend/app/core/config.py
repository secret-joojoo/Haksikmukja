import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:////data/haksik.db"
    
    # API 키
    GEMINI_API_KEY: str

    # .env 파일에 DISCORD_WEBHOOK_URL=... 형식으로 추가해야 해!
    DISCORD_WEBHOOK_URL: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()