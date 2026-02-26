from sqlalchemy.orm import Session
from app.models import NewsArticle
from app.models.article_sentiment import ArticleSentiment

def save_articles(db:Session,ticker:str,articles: list):
    saved =[]

    for a in articles:

        exists =db.query(NewsArticle).filter(NewsArticle.url == a["url"]).first()

        if exists:
            continue
        article = NewsArticle(
           ticker=ticker,
           title=a["title"],
           description=a.get("description"),
           url=a["url"],
           source=a["source"]["name"] if a.get("source") else None,
           published_at=a.get("publishedAt")

        )

        db.add(article)
        saved.append(article)
        db.commit()

        return saved
    
def get_articles(db:Session,ticker: str):
    return(
      db.query(NewsArticle)
      .filter(NewsArticle.ticker == ticker)
      .order_by(NewsArticle.published_at.desc())
      .limit(20)
      .all()

    )

def get_articles_without_sentiment(db,ticker:str):
    return (
      db.query(NewsArticle)
      .outerjoin(ArticleSentiment,NewsArticle.id == ArticleSentiment.article_id)
        .filter(NewsArticle.ticker == ticker)
        .filter(ArticleSentiment.id == None)
        .all()


    )

def save_sentiment(db,article_id: int,label:str,score:float):
    sentiment = ArticleSentiment(
        article_id=article_id,
        label=label,
        score=score
    )
    db.add(sentiment)
    db.commit()
