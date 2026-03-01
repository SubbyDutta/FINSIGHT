from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint
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

    label = Column(String(20))  
    score = Column(Float)

    processed_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    __table_args__ = (
        UniqueConstraint("article_id", name="idx_sentiment_article_id"),
    )
    article = relationship("NewsArticle")