from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.services.ohlcv_service import fetch_and_store_ohlcv
from app.services.chat_service import generate_explanation

 



router = APIRouter(prefix="/fetchHistory", tags=["Historical"])


@router.get("/{ticker}")

def fetch_history(ticker: str, db: Session = Depends(get_db)):
    result = fetch_and_store_ohlcv(db, ticker)
    

    return {
        "ticker": result["ticker"],
        "rows_inserted": result["rows_inserted"]
    }