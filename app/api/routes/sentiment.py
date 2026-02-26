from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.services.sentiment_service import (
    process_ticker_sentiment,
    get_sentiment_summary,
)
from app.schemas.sentiment import SentimentSummary

router = APIRouter(prefix="/sentiment", tags=["Sentiment"])


@router.get("/{ticker}", response_model=SentimentSummary)
def sentiment(ticker: str, db: Session = Depends(get_db)):

   
    process_ticker_sentiment(db, ticker)

   
    return get_sentiment_summary(db, ticker)