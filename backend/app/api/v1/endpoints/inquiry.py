from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db import models
from app.schemas.inquiry import InquiryCreate
from app.core.config import settings
import httpx

router = APIRouter()

@router.post("/")
async def create_inquiry(inquiry: InquiryCreate, db: AsyncSession = Depends(get_db)):
    # 1. DB에 저장
    db_inquiry = models.Inquiry(
        category=inquiry.category,
        content=inquiry.content
    )
    db.add(db_inquiry)
    await db.commit()
    
    # 2. 디스코드로 알림 발송 (웹훅 URL이 있을 때만)
    if settings.DISCORD_WEBHOOK_URL:
        async with httpx.AsyncClient() as client:
            payload = {
                "content": f"📢 **[학식묵자] 새로운 문의 접수!**\n\n**분류**: {inquiry.category}\n**내용**: {inquiry.content}"
            }
            try:
                await client.post(settings.DISCORD_WEBHOOK_URL, json=payload)
            except Exception as e:
                print(f"디스코드 전송 실패: {e}")
                # 알림 실패해도 DB 저장은 성공했으니 에러를 띄우진 않음

    return {"message": "성공적으로 접수되었습니다."}