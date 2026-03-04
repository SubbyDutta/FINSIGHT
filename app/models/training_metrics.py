from sqlalchemy import Column, Integer, Float, String, TIMESTAMP
from sqlalchemy.sql import func
from app.db.base import Base


class TrainingMetric(Base):
    __tablename__ = "training_metrics"

    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(50), index=True)
    epoch = Column(Integer)

    train_loss = Column(Float)
    val_loss = Column(Float)

    train_rmse = Column(Float)
    val_rmse = Column(Float)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())