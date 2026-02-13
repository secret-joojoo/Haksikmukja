from pydantic import BaseModel

class InquiryCreate(BaseModel):
    category: str
    content: str