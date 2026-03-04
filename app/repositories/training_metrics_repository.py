from sqlalchemy.orm import Session
from app.models.training_metrics import TrainingMetric


def save_training_metric(
    db: Session,
    model_version: str,
    epoch: int,
    train_loss: float,
    val_loss: float,
    train_rmse: float,
    val_rmse: float,
):
    metric = TrainingMetric(
        model_version=model_version,
        epoch=epoch,
        train_loss=train_loss,
        val_loss=val_loss,
        train_rmse=train_rmse,
        val_rmse=val_rmse,
    )

    db.add(metric)
    db.commit()