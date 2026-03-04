from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.services.ohlcv_service import fetch_and_store_ohlcv


router = APIRouter(prefix="/ohlcv", tags=["OHLCV"])


@router.get("/fetch/{ticker}")
def fetch_ohlcv_history(
    ticker: str,
    period: str = Query(default="2y"),
    interval: str = Query(default="1d"),
    db: Session = Depends(get_db),
):
    try:
        return fetch_and_store_ohlcv(
            db=db,
            ticker=ticker,
            period=period,
            interval=interval,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
