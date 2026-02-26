from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class ArticleEmbedding(Base):
    __tablename__ = "article_embeddings"

    id = Column(Integer, primary_key=True, index=True)

    article_id = Column(
        Integer,
        ForeignKey("news_articles.id", ondelete="CASCADE"),
        nullable=False
    )

    embedding_id = Column(String(100), index=True)

    embedded_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    article = relationship("NewsArticle")