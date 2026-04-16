"""Chatbot API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from config import get_logger
from models.database import get_db
from services.ai_service import process_query

logger = get_logger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    
    @validator('question')
    def question_not_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('Question cannot be empty')
        return v


@router.post("/chatbot", response_model=None)
async def chatbot(req: ChatRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    """Process a user query via the AI chatbot."""
    try:
        logger.info(f"Chatbot query: {req.question[:100]}...")  # Log truncated for privacy
        return await process_query(req.question, db)
    except Exception as e:
        logger.error(f"Chatbot error: {e}")
        return {"answer": "Sorry, I encountered an error processing your question. Please try again."}
