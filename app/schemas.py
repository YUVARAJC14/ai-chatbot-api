from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Optional

class MessageCreate(BaseModel):
    content: str

class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class ConversationOut(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ConversationDetailOut(ConversationOut):
    messages: List[MessageOut] = []