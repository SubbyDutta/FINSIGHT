from app.integrations.yfinance_client import fetch_stock_quote


INDIAN_DEFAULT_SUFFIX = ".NS"


def normalize_ticker(ticker: str) -> str:
    ticker = ticker.strip().upper()

    
    if "." in ticker:
        return ticker

   
    return ticker + INDIAN_DEFAULT_SUFFIX


def get_stock_quote(ticker: str):
    if not ticker or len(ticker) > 15:
        raise ValueError("Invalid ticker")

    normalized = normalize_ticker(ticker)

    return fetch_stock_quote(normalized)