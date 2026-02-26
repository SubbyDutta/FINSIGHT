import requests
from app.core.config import settings


BASE_URL = "https://newsapi.org/v2/everything"


def fetch_news(query: str):

    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 20,
        "apiKey": settings.NEWS_API_KEY,
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
    except requests.exceptions.RequestException:
        raise Exception("Failed to connect to NewsAPI")

    
    if response.status_code != 200:
        raise Exception(f"NewsAPI HTTP error: {response.status_code}")

    
    try:
        data = response.json()
    except ValueError:
        raise Exception("NewsAPI returned invalid JSON")

    
    if data.get("status") != "ok":
        raise Exception(f"NewsAPI error: {data.get('message')}")

    return data.get("articles", [])