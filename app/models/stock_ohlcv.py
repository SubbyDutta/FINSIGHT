from sqlalchemy import Column, String, DateTime, Numeric, BigInteger, UniqueConstraint
from app.db.base import Base
from sqlalchemy.sql import func


class StockOHLCV(Base):
    __tablename__ = "stock_ohlcv"

    time = Column(DateTime(timezone=True), primary_key=True)
    ticker = Column(String, primary_key=True)

    open = Column(Numeric)
    high = Column(Numeric)
    low = Column(Numeric)
    close = Column(Numeric)
    volume = Column(BigInteger)

    rsi = Column(Numeric)
    macd = Column(Numeric)
    bb_upper = Column(Numeric)
    bb_lower = Column(Numeric)
    ma_7 = Column(Numeric)
    ma_21 = Column(Numeric)

    __table_args__ = (
        UniqueConstraint("ticker", "time", name="uq_stock_ohlcv_ticker_time"),
    )