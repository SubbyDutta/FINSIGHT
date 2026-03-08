from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.schemas.chat import ChatRequest
from app.services.chat_service import generate_explanation





router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        return generate_explanation(
            db,
            req.ticker,
            req.question,
            top_k=req.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
