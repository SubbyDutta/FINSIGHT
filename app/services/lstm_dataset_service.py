from typing import List

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.stock_service import normalize_ticker
from app.api.ai.lstm.sequence_builder import build_sequences
import numpy as np
def fetch_ohlcv_data(session: Session, ticker: str) -> pd.DataFrame:
    query = text("""
        SELECT
            time,
            ticker,
            open,
            high,
            low,
            close,
            volume,
            rsi,
            macd,
            bb_upper,
            bb_lower,
            ma_7,
            ma_21,
            time::date AS day
        FROM stock_ohlcv
        WHERE ticker = :ticker
        ORDER BY time ASC
    """)

    result = session.execute(query, {"ticker": ticker}).mappings().all()

    if not result:
        raise ValueError("No OHLCV data found")

    return pd.DataFrame(result)

   


def fetch_daily_sentiment(session: Session, ticker: str) -> pd.DataFrame:
    query = text("""
        SELECT
            na.published_at::date AS day,
            AVG(asent.score) AS sentiment_score
        FROM news_articles na
        JOIN article_sentiment asent
            ON na.id = asent.article_id
        WHERE na.ticker = :ticker
        GROUP BY day
        ORDER BY day ASC
    """)

    result = session.execute(query, {"ticker": ticker}).mappings().all()

    if not result:
        return pd.DataFrame(columns=["day", "sentiment_score"])

    return pd.DataFrame(result)
    

def build_lstm_feature_dataset(session: Session, ticker: str) -> pd.DataFrame:

    ticker = normalize_ticker(ticker)

    ohlcv_df = fetch_ohlcv_data(session, ticker)
    sentiment_df = fetch_daily_sentiment(session, ticker)

    merged = pd.merge(
        ohlcv_df,
        sentiment_df,
        on="day",
        how="left"
    )

    merged["sentiment_score"] = merged["sentiment_score"].fillna(0.0)

    return merged

def build_multi_ticker_sequences(session: Session,tickers: List[str]):

    all_X=[]
    all_y=[]
    for ticker in tickers:
        df=build_lstm_feature_dataset(session,ticker)
        
        X,y=build_sequences(df)
        if len(X) == 0:
            continue
        all_X.append(X)
        all_y.append(y)

    if not all_X:
        raise ValueError("No valid data found for any ticker")
    X_combined=np.vstack(all_X)
    y_combined=np.vstack(all_y)    
    print(f"Combined dataset → X shape: {X_combined.shape}, y shape: {y_combined.shape}")

    return X_combined,y_combined