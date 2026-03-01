import yfinance as yf
import pandas as pd
from sqlalchemy.orm import Session

from app.api.ai.indicators import add_technical_indicators
from app.repositories.ohlcv_repository import bulk_insert_ohlcv
from app.services.stock_service import normalize_ticker

REQUIRED_OHLCV_COLUMNS = {"time", "open", "high", "low", "close", "volume"}


def _normalize_ohlcv_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
      
        df.columns = df.columns.get_level_values(0)

    df = df.rename(
        columns={
            "Date": "time",
            "Datetime": "time",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )

    missing = REQUIRED_OHLCV_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing OHLCV columns after yfinance fetch: {sorted(missing)}. "
            f"Available columns: {list(df.columns)}"
        )
    return df


def fetch_and_store_ohlcv(
    db:Session,
    ticker:str,
    period:str="2y",
    interval:str="1d"  
):
    ticker=normalize_ticker(ticker)
    df=yf.download(ticker,period=period,interval=interval)
    if df.empty:
        raise ValueError(f"No data found for ticker {ticker}")
    df.reset_index(inplace=True)
    df = _normalize_ohlcv_columns(df)

    df=add_technical_indicators(df)
    df["ticker"]=ticker
    df.dropna(inplace=True)
    records=df.to_dict(orient="records")
    if not records:
        return {
            "ticker": ticker,
            "rows_inserted": 0
        }
    bulk_insert_ohlcv(db,records)

    return{
        "ticker": ticker,
        "rows_inserted": len(records)
    }
    


