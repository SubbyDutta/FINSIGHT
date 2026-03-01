from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db 
from app.services.lstm_training_service import train_global_lstm

router = APIRouter()

@router.post("/train/lstm")
def train_lstm(db: Session = Depends(get_db)):

    tickers = ["TCS", "WIPRO", "RELIANCE"]

    result = train_global_lstm(db, tickers)

    return result