from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.services.lstm_dataset_service import build_lstm_feature_dataset
from app.services.ohlcv_service import fetch_and_store_ohlcv
from app.services.chat_service import generate_explanation

 



router = APIRouter(prefix="/fetchHistory", tags=["Historical"])


@router.get("/{ticker}")

@router.get("/{ticker}")
def test2(ticker: str, db: Session = Depends(get_db)):
    dataset = build_lstm_feature_dataset(db, ticker)

    return {
        "ticker": ticker,
        "dataset_preview": dataset.columns.tolist()
    }