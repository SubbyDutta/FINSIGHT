from langchain.tools import tool

from app.services.stock_service import get_stock_quote
from app.services.sentiment_service import get_sentiment_summary
from app.services.lstm_inference_service import predict_ticker
from app.services.news_service import get_articles
from app.services.ohlcv_service import get_latest_indicators


@tool
def fetch_stock_price(ticker: str):
    """Get the latest stock price and percent change."""
    data = get_stock_quote(ticker)

    return {
        "ticker": data["ticker"],
        "price": data["price"],
        "change_percent": data["change_percent"]
    }


@tool
def get_sentiment_summary_tool(ticker: str):
    """Get aggregated sentiment for a ticker."""
    data = get_sentiment_summary(ticker)

    return {
        "label": data["label"],
        "score": data["score"],
        "article_count": data["article_count"]
    }


@tool
def get_price_prediction_tool(ticker: str):
    """Get LSTM 5-day forecast and signal."""
    data = predict_ticker(ticker)

    return {
        "forecast_5d": data["forecast_5d"],
        "signal": data["signal"],
        "confidence": data["confidence"],
        "model_version": data["model_version"]
    }


@tool
def get_recent_news_tool(ticker: str):
    """Retrieve latest news headlines for the ticker."""
    articles = get_articles(ticker)

    headlines = []

    for article in articles[:5]:
        headlines.append(article["title"])

    return {
        "headlines": headlines
    }


@tool
def get_technical_analysis_tool(ticker: str):
    """Get latest technical indicators."""

    indicators = get_latest_indicators(ticker)

    if not indicators:
        return {"error": "No indicator data"}

    rsi = indicators["rsi"]
    close = indicators["close"]
    bb_upper = indicators["bb_upper"]
    bb_lower = indicators["bb_lower"]

    if rsi > 70:
        rsi_signal = "overbought"
    elif rsi < 30:
        rsi_signal = "oversold"
    else:
        rsi_signal = "neutral"

    if close >= bb_upper:
        bb_position = "upper_band"
    elif close <= bb_lower:
        bb_position = "lower_band"
    else:
        bb_position = "middle"

    overall_signal = "HOLD"

    if rsi_signal == "oversold":
        overall_signal = "BUY"

    if rsi_signal == "overbought":
        overall_signal = "SELL"

    return {
        "rsi": rsi,
        "macd": indicators["macd"],
        "bb_position": bb_position,
        "overall_signal": overall_signal
    }