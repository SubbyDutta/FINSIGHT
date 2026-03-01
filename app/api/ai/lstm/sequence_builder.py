import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "rsi",
    "macd",
    "bb_upper",
    "bb_lower",
    "ma_7",
    "ma_21",
    "sentiment_score"
]


def build_sequences(df, lookback=60, horizon=5):

    df = df.sort_values("time").reset_index(drop=True)

    features = df[FEATURE_COLUMNS].astype(float).values
    closes = df["close"].astype(float).values

    X = []
    y = []

    for i in range(lookback, len(df)):

        if i + horizon > len(df):
            break

        X_window = features[i - lookback:i]
        y_window = closes[i:i + horizon]

        if len(y_window) == horizon:
            X.append(X_window)
            y.append(y_window)

    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.float32)

    return X, y