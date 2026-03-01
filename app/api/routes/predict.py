from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.deps import get_db
from app.services.lstm_inference_service import predict_ticker


router = APIRouter(prefix="/predict", tags=["prediction"])


@router.get("/{ticker}")
def predict_endpoint(ticker: str, db: Session = Depends(get_db)):
    try:
        return predict_ticker(db, ticker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{ticker}/signal")
def predict_signal_endpoint(ticker: str, db: Session = Depends(get_db)):
    result = predict_ticker(db, ticker)

    return {
        "ticker": result["ticker"],
        "signal": result["signal"],
        "confidence": result["confidence"],
        "model_version": result["model_version"],
    }