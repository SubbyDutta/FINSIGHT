import pandas as pd
import pandas_ta as ta


def _safe_indicator_column(indicator_df: pd.DataFrame | None, prefix: str) -> pd.Series | None:
    if indicator_df is None or indicator_df.empty:
        return None
    for col in indicator_df.columns:
        if str(col).startswith(prefix):
            return indicator_df[col]
    return None


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    close = pd.to_numeric(df["close"], errors="coerce")

    df["rsi"] = ta.rsi(close, length=14)

    macd = ta.macd(close)
    macd_col = _safe_indicator_column(macd, "MACD_")
    df["macd"] = macd_col if macd_col is not None else pd.NA

    bb = ta.bbands(close, length=20)
    bb_upper_col = _safe_indicator_column(bb, "BBU_")
    bb_lower_col = _safe_indicator_column(bb, "BBL_")
    df["bb_upper"] = bb_upper_col if bb_upper_col is not None else pd.NA
    df["bb_lower"] = bb_lower_col if bb_lower_col is not None else pd.NA

    df["ma_7"] = ta.sma(close, length=7)
    df["ma_21"] = ta.sma(close, length=21)

    return df
