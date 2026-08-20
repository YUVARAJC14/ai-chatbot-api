from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class MessageCreate(BaseModel):
    content: str

class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class ConversationOut(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ConversationDetailOut(ConversationOut):
    messages: List[MessageOut] = []