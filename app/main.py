from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.llm import get_ai_reply
from fastapi.responses import StreamingResponse, FileResponse
from app.llm import stream_ai_reply
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="AI Chatbot API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def health_check():
    return {"status": "ok", "message": "AI Chatbot API is running!"}

@app.post("/conversations", response_model=schemas.ConversationOut)
def create_conversation(
    payload: schemas.ConversationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    conversation = models.Conversation(
        user_id=current_user.id,
        title=payload.title
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

@app.post("/conversations/{conversation_id}/messages", response_model=schemas.MessageOut)
@limiter.limit("5/minute")
def create_message(
    request: Request,
    conversation_id: int,
    payload: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Check if the conversation belongs to the current user
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Create the message
    user_message = models.Message(
        conversation_id=conversation_id,
        role="user",
        content=payload.content
    )
    db.add(user_message)
    db.commit()

    MAX_HISTORY_LENGTH = 10

    recent_messages = conversation.messages[-MAX_HISTORY_LENGTH:]
    history = [
        {"role": m.role, "content": m.content}
        for m in recent_messages
    ]

    ai_reply_text = get_ai_reply(history)

    ai_message = models.Message(
        conversation_id=conversation_id,
        role="assistant",
        content=ai_reply_text
    )
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)

    return ai_message

@app.post("/conversations/{conversation_id}/messages/stream")
@limiter.limit("5/minute")
def send_message_stream(
    request: Request,
    conversation_id: int,
    payload: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Check if the conversation belongs to the current user
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Create the user message
    user_message = models.Message(
        conversation_id=conversation_id,
        role="user",
        content=payload.content
    )
    db.add(user_message)
    db.commit()

    MAX_HISTORY_LENGTH = 10
    recent_messages = conversation.messages[-MAX_HISTORY_LENGTH:]
    history = [
        {"role": m.role, "content": m.content}
        for m in recent_messages
    ]

    # Stream the AI reply
    def event_generator():
        full_reply = ""
        for chunk in stream_ai_reply(history):
            full_reply += chunk
            yield f"data: {chunk}\n\n"

        ai_message = models.Message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_reply
        )
        db.add(ai_message)
        db.commit()

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/conversations", response_model=List[schemas.ConversationOut])
def list_conversations(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    conversations = (
        db.query(models.Conversation)
        .filter(models.Conversation.user_id == current_user.id).offset(skip).limit(limit).all()
    )
    return conversations

@app.get("/conversations/{conversation_id}", response_model=schemas.ConversationDetailOut)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id,
        models.Conversation.user_id == current_user.id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation

@app.get("/chat")
def serve_chat_ui():
    return FileResponse("static/index.html")
