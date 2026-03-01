from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, func
from app.db.base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(100), index=True)
    predicted_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    forecast_day_1 = Column(DECIMAL(12, 4))
    forecast_day_2 = Column(DECIMAL(12, 4))
    forecast_day_3 = Column(DECIMAL(12, 4))
    forecast_day_4 = Column(DECIMAL(12, 4))
    forecast_day_5 = Column(DECIMAL(12, 4))

    signal = Column(String(10))
    confidence = Column(DECIMAL(5, 4))
    model_version = Column(String(50))