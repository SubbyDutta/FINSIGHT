from pydantic import BaseModel
from datetime import datetime


class StockQuote(BaseModel):
    ticker: str
    price: float
    change: float
    change_percent: float
    currency: str
    market_time: datetime