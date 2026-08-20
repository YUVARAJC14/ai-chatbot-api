from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.auth import get_current_user
from app.llm import get_ai_reply
from fastapi.responses import StreamingResponse
from app.llm import stream_ai_reply

app = FastAPI(title="AI Chatbot API")

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
def create_message(
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

    history = [
        {"role": m.role, "content": m.content}
        for m in conversation.messages
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
def send_message_stream(
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

    history = [
        {"role": m.role, "content": m.content}
        for m in conversation.messages
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