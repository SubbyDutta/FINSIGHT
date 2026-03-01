import os
import torch
import joblib
import numpy as np
from sqlalchemy.orm import Session

from app.api.ai.lstm.model import LSTMForecaster
from app.api.ai.lstm.sequence_builder import FEATURE_COLUMNS
from app.services.lstm_dataset_service import build_lstm_feature_dataset
from app.repositories.prediction_repository import save_prediction
from app.services.stock_service import normalize_ticker


MODEL_VERSION = "lstm_global_v1"
ARTIFACT_DIR = "ai/lstm/artifacts/global_v1"

_model = None
_feature_scaler = None
_target_scaler = None


def _load_artifacts():
    global _model, _feature_scaler, _target_scaler

    if _model is None:
        model = LSTMForecaster(
            input_size=12,
            hidden_size=64,
            num_layers=2,
            output_size=5,
            dropout=0.2,
        )
        model.load_state_dict(
            torch.load(os.path.join(ARTIFACT_DIR, "lstm_model.pt"), map_location="cpu")
        )
        model.eval()
        _model = model

    if _feature_scaler is None:
        _feature_scaler = joblib.load(
            os.path.join(ARTIFACT_DIR, "feature_scaler.pkl")
        )

    if _target_scaler is None:
        _target_scaler = joblib.load(
            os.path.join(ARTIFACT_DIR, "target_scaler.pkl")
        )


def predict_ticker(db: Session, ticker: str):

    ticker = normalize_ticker(ticker)

    _load_artifacts()

    df = build_lstm_feature_dataset(db, ticker)

    if len(df) < 60:
        raise ValueError("Not enough data for prediction (requires 60 days)")

    missing = [col for col in FEATURE_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required features for inference: {missing}")

    df_last_60 = df.tail(60)
    features = df_last_60[FEATURE_COLUMNS].apply(
        lambda col: np.asarray(col, dtype=np.float32)
    )

    X = features.to_numpy(dtype=np.float32)
    X = X.reshape(1, 60, 12)

    X_flat = X.reshape(-1, 12)
    X_scaled = _feature_scaler.transform(X_flat)
    X_scaled = X_scaled.reshape(1, 60, 12)

    X_tensor = torch.tensor(X_scaled, dtype=torch.float32)

    with torch.no_grad():
        prediction_scaled = _model(X_tensor).numpy()

    
    prediction = _target_scaler.inverse_transform(prediction_scaled)[0]

    current_close = float(df_last_60["close"].iloc[-1])

    expected_return = (prediction[-1] - current_close) / current_close

    signal, confidence = generate_signal(expected_return)

    
    save_prediction(
        db=db,
        ticker=ticker,
        forecast=prediction.tolist(),
        signal=signal,
        confidence=confidence,
        model_version=MODEL_VERSION,
    )

    return {
        "ticker": ticker,
        "forecast_5d": prediction.tolist(),
        "signal": signal,
        "confidence": confidence,
        "model_version": MODEL_VERSION,
    }


def generate_signal(expected_return: float):

    abs_return = abs(expected_return)

    if expected_return > 0.02:
        signal = "BUY"
    elif expected_return < -0.02:
        signal = "SELL"
    else:
        signal = "HOLD"

    confidence = min(abs_return * 10, 0.99)

    return signal, round(confidence, 4)
