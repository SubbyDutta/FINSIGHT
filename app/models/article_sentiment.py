from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class ArticleSentiment(Base):
    __tablename__ = "article_sentiment"

    id = Column(Integer, primary_key=True, index=True)

    article_id = Column(
        Integer,
        ForeignKey("news_articles.id", ondelete="CASCADE"),
        nullable=False
    )

    label = Column(String(20))   # positive / negative / neutral
    score = Column(Float)

    processed_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    article = relationship("NewsArticle")