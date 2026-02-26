from fastapi import APIRouter, HTTPException
from app.schemas.stock import StockQuote
from app.services.stock_service import get_stock_quote

router = APIRouter(prefix="/stock", tags=["Stock"])


@router.get("/{ticker}", response_model=StockQuote)
def read_stock(ticker: str):
    try:
        data = get_stock_quote(ticker)
        return data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))