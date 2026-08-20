from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

def get_current_user(
        x_api_key: str = Header(...),
        db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.api_key == x_api_key).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return user