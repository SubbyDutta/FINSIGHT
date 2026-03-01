import os
import numpy as np

from app.services.lstm_dataset_service import build_multi_ticker_sequences
from app.api.ai.lstm.data_pipeline import time_series_split, scale_data
from app.api.ai.lstm.trainer import train_model


MODEL_DIR = "ai/lstm/artifacts/global_v1"


def train_global_lstm(session, tickers):

    print("Building multi-ticker dataset...")
    X, y = build_multi_ticker_sequences(session, tickers)

    print("Splitting dataset...")
    X_train, X_val, y_train, y_val = time_series_split(X, y)

    print("Scaling features...")
    X_train_scaled, X_val_scaled, y_train_scaled, y_val_scaled, feature_scaler, target_scaler = scale_data(
        X_train, X_val, y_train,y_val,save_path=MODEL_DIR
    )

    print("Training model...")
    model = train_model(
    X_train_scaled,
    y_train_scaled,  
    X_val_scaled,
    y_val_scaled,    
    model_save_path=MODEL_DIR,
    epochs=30,
    batch_size=32,
    lr=0.001,
    device="cpu"
)

    print("Training completed.")
    print("Model saved to:", os.path.join(MODEL_DIR, "lstm_model.pt"))

    return {
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "model_path": os.path.join(MODEL_DIR, "lstm_model.pt")
    }