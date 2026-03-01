import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
import os


def time_series_split(X, y, train_ratio=0.8):

    train_size = int(len(X) * train_ratio)

    X_train = X[:train_size]
    y_train = y[:train_size]

    X_val = X[train_size:]
    y_val = y[train_size:]

    return X_train, X_val, y_train, y_val

 
def scale_data(X_train, X_val, y_train, y_val, save_path=None):

    num_samples, seq_len, num_features = X_train.shape

    
    feature_scaler = StandardScaler()

    X_train_reshaped = X_train.reshape(-1, num_features)
    feature_scaler.fit(X_train_reshaped)

    X_train_scaled = feature_scaler.transform(X_train_reshaped)
    X_train_scaled = X_train_scaled.reshape(num_samples, seq_len, num_features)

    val_samples = X_val.shape[0]
    X_val_reshaped = X_val.reshape(-1, num_features)
    X_val_scaled = feature_scaler.transform(X_val_reshaped)
    X_val_scaled = X_val_scaled.reshape(val_samples, seq_len, num_features)

    
    target_scaler = StandardScaler()

    target_scaler.fit(y_train)

    y_train_scaled = target_scaler.transform(y_train)
    y_val_scaled = target_scaler.transform(y_val)

    if save_path:
        os.makedirs(save_path, exist_ok=True)
        joblib.dump(feature_scaler, os.path.join(save_path, "feature_scaler.pkl"))
        joblib.dump(target_scaler, os.path.join(save_path, "target_scaler.pkl"))

    return (
        X_train_scaled,
        X_val_scaled,
        y_train_scaled,
        y_val_scaled,
        feature_scaler,
        target_scaler
    )