from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.schemas.chat import ChatRequest
from app.services.chat_service import generate_explanation





router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/")
def chat(req: ChatRequest, db: Session = Depends(get_db)):

    answer, sources = generate_explanation(
        db,
        req.ticker,
        req.question
    )

    return {
        "answer": answer,
        "sources": sources
    }