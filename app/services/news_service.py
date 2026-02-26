
from app.integrations.newsapi_client import fetch_news
from app.repositories.article_repo import save_articles,get_articles
from app.services.stock_service import normalize_ticker

def ingest_news(db,ticker: str):
    ticker = normalize_ticker(ticker)

    search_query = ticker.split(".")[0]

    articles = fetch_news(search_query)

    saved = save_articles(db,ticker,articles)

    return saved 

def fetch_stored_news(db,ticker:str):
    ticker = normalize_ticker(ticker)
    return get_articles(db,ticker)
