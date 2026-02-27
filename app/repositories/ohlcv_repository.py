from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List, Dict


def bulk_insert_ohlcv(session: Session, records: List[Dict]):
    insert_query = text("""
        INSERT INTO stock_ohlcv (
            time, ticker, open, high, low, close, volume,
            rsi, macd, bb_upper, bb_lower, ma_7, ma_21
        )
        VALUES (
            :time, :ticker, :open, :high, :low, :close, :volume,
            :rsi, :macd, :bb_upper, :bb_lower, :ma_7, :ma_21
        )
        ON CONFLICT (ticker, time) DO UPDATE
        SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume,
            rsi = EXCLUDED.rsi,
            macd = EXCLUDED.macd,
            bb_upper = EXCLUDED.bb_upper,
            bb_lower = EXCLUDED.bb_lower,
            ma_7 = EXCLUDED.ma_7,
            ma_21 = EXCLUDED.ma_21
    """)

    session.execute(insert_query, records)
    session.commit()