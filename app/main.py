from fastapi import FastAPI
from app.db.base import Base
from app.db.session import engine

from app.models import NewsArticle, ArticleSentiment, ArticleEmbedding 
from app.api.routes.stock import router as stock_router
from app.api.routes.news import router as news_router
from app.api.routes.sentiment import router as sentiment_router
from app.api.routes.chat import router as chat_router

app = FastAPI(title="FinSight AI")

Base.metadata.create_all(bind=engine)

app.include_router(stock_router)
app.include_router(news_router)
app.include_router(sentiment_router)
app.include_router(chat_router)
@app.get("/")
def root():
    return {"message": "FinSight AI running"}