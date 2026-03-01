from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.db.base import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True)

    ticker = Column(String(10), index=True)

    title = Column(Text, nullable=False)
    description = Column(Text)

    url = Column(Text, unique=True, index=True)
    source = Column(String(100))

    published_at = Column(DateTime(timezone=True))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    __table_args__ = (
        UniqueConstraint("ticker", "published_at", name="dx_news_ticker_published"),
    )