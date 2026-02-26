from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.schemas.article import ArticleOut
from app.services.news_service import ingest_news, fetch_stored_news

router = APIRouter(prefix="/news", tags=["News"])


@router.get("/{ticker}", response_model=list[ArticleOut])
def get_news(ticker: str, db: Session = Depends(get_db)):

  
    ingest_news(db, ticker)

   
    return fetch_stored_news(db, ticker) 