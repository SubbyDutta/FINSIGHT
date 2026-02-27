from app.api.ai.finbert import analyze_sentiment
from app.repositories.article_repo import get_articles_without_sentiment,save_sentiment
from app.services.stock_service import normalize_ticker
from sqlalchemy import func
from app.models.article_sentiment import ArticleSentiment
from app.models import NewsArticle
from app.api.ai.vector_store import add_article_embedding


def process_ticker_sentiment(db,ticker:str):
    ticker = normalize_ticker(ticker)

    articles=get_articles_without_sentiment(db,ticker)
    processed=0

    for article in articles:
        text= article.title or ""
        if article.description:
            text += " " + article.description
        label,score = analyze_sentiment(text)
        save_sentiment(db,article.id,label,score)
        add_article_embedding(article.id,text)
        processed +=1
    return processed

def get_sentiment_summary(db,ticker:str):
    ticker=normalize_ticker(ticker)
    results=(
        db.query(
            ArticleSentiment.label,
            func.count(ArticleSentiment.id)
        )
        .join(NewsArticle,NewsArticle.id == ArticleSentiment.article_id)
        .filter(NewsArticle.ticker == ticker)
        .group_by(ArticleSentiment.label)
        .all()

    )
    summary = {"positive":0,"negative":0,"neutral":0}

    for label,count in results:
        summary[label]=count

    total = sum(summary.values())
    if total == 0:
        return{"message":"No sentiment data available for this ticker"}
    score = (summary["positive"] - summary["negative"])/total 
    return {
        "counts": summary,
        "sentiment_score": round(score, 3),
        "interpretation":
            "Bullish" if score > 0.2
            else "Bearish" if score < -0.2
            else "Neutral"
    }