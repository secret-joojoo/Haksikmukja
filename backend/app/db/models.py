from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base
from sqlalchemy.sql import func # 자동으로 시간 넣기 위해 필요

# 1. 학교 테이블
class School(Base):
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # 학교 이름 (예: 한국대학교)
    region = Column(String)  # 지역 (예: 서울)

    # 식당과의 관계 설정 (1:N)
    cafeterias = relationship("Cafeteria", back_populates="school")

# 2. 식당 테이블
class Cafeteria(Base):
    __tablename__ = "cafeterias"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id")) # 어느 학교 소속인지
    name = Column(String)  # 식당 이름 (예: 제1학생회관)
    url = Column(String)   # 크롤링할 학식 사이트 주소

    school = relationship("School", back_populates="cafeterias")
    menus = relationship("Menu", back_populates="cafeteria")

# 3. 메뉴 테이블
class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    cafeteria_id = Column(Integer, ForeignKey("cafeterias.id")) # 어느 식당 메뉴인지
    date = Column(Date, index=True) # 날짜 (2026-01-16)
    meal_type = Column(String)      # 식사 종류 (BREAKFAST, LUNCH, DINNER)
    menu_text = Column(Text)        # 메뉴 내용 (소세지야채볶음, 쌀밥...)
    
    # AI 이미지 URL 저장 공간
    image_url_2d = Column(String, nullable=True) # 2D 이미지 경로
    image_url_3d = Column(String, nullable=True) # 3D 뷰어용 경로

    cafeteria = relationship("Cafeteria", back_populates="menus")

# 4. 고객 문의 테이블 (가장 아래에 추가)
class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String)    # 문의 사유 (버그, 제안 등)
    content = Column(Text)       # 상세 내용
    created_at = Column(DateTime, default=func.now()) # 생성 시간