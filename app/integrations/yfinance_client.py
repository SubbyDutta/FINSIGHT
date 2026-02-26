import yfinance as yf
from datetime import datetime, timezone


def fetch_stock_quote(ticker: str):

    stock = yf.Ticker(ticker)

     
    try:
        info = stock.fast_info

        current_price = info["last_price"]
        prev_close = info["previous_close"]

        if current_price is None or prev_close is None:
            raise Exception("fast_info missing")

    except Exception:
        
        daily = stock.history(period="5d", interval="1d", auto_adjust=False)

        if daily.empty:
            raise ValueError("Ticker not found")

        last_day = daily.iloc[-1]
        prev_day = daily.iloc[-2]

        current_price = float(last_day["Close"])
        prev_close = float(prev_day["Close"])

    change = current_price - prev_close
    change_percent = (change / prev_close) * 100

    return {
        "ticker": ticker,
        "price": round(current_price, 2),
        "change": round(change, 2),
        "change_percent": round(change_percent, 2),
        "currency": "INR",
        "market_time": datetime.now(timezone.utc),
    }