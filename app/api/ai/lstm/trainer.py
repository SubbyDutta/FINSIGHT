import math

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import os

from app.api.ai.lstm.model import LSTMForecaster
from app.db import session
from app.repositories.training_metrics_repository import save_training_metric


def train_model(
    X_train,
    y_train,
    X_val,
    y_val,
    model_save_path,
    max_epochs=300,
    patience=12,
    min_delta=1e-4,
    batch_size=32,
    lr=0.001,
    max_grad_norm=1.0,
    device="cpu",
    session=session,
):

    device = torch.device(device)

    model = LSTMForecaster().to(device)

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=0.5,
        patience=max(1, patience // 2),
        min_lr=1e-6,
    )

    train_dataset = TensorDataset(
        torch.tensor(X_train, dtype=torch.float32),
        torch.tensor(y_train, dtype=torch.float32)
    )

    val_dataset = TensorDataset(
        torch.tensor(X_val, dtype=torch.float32),
        torch.tensor(y_val, dtype=torch.float32)
    )

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=False)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    if len(train_loader) == 0 or len(val_loader) == 0:
        raise ValueError("Empty train/validation loader. Check sequence generation and split.")

    best_val_loss = float("inf")
    epochs_without_improvement = 0

    for epoch in range(max_epochs):

        model.train()
        train_loss = 0.0


        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)

            optimizer.zero_grad()
            preds = model(xb)
            loss = criterion(preds, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
            optimizer.step()

            train_loss += loss.item()

        train_loss /= len(train_loader)
        train_rmse = math.sqrt(train_loss)

        model.eval()
        val_loss = 0.0

        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                preds = model(xb) 
                loss = criterion(preds, yb)
                val_loss += loss.item()

        val_loss /= len(val_loader)
        val_rmse = math.sqrt(val_loss)
        scheduler.step(val_loss)
        current_lr = optimizer.param_groups[0]["lr"]

        print(
        f"Epoch {epoch+1}/{max_epochs} | "
        f"Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f} | "
        f"Train RMSE: {train_rmse:.6f} | Val RMSE: {val_rmse:.6f} | "
        f"LR: {current_lr:.6g}"
    )

        if val_loss < (best_val_loss - min_delta):
            best_val_loss = val_loss
            epochs_without_improvement = 0
            os.makedirs(model_save_path, exist_ok=True)
            torch.save(model.state_dict(), os.path.join(model_save_path, "lstm_model.pt"))
        else:
            epochs_without_improvement += 1

        save_training_metric(
        db=session,
        model_version="lstm_global_v1",
        epoch=epoch + 1,
        train_loss=train_loss,
        val_loss=val_loss,
        train_rmse=train_rmse,
        val_rmse=val_rmse,
        )    

        if epochs_without_improvement >= patience:
            print(
                f"Early stopping triggered at epoch {epoch + 1}. "
                f"Best Val Loss: {best_val_loss:.6f}"
            )
            break

    return model
