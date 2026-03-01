from sqlalchemy.orm import Session
from app.models.prediction import Prediction


def save_prediction(
    db: Session,
    ticker: str,
    forecast: list[float],
    signal: str,
    confidence: float,
    model_version: str,
):
    prediction = Prediction(
        ticker=ticker,
        forecast_day_1=forecast[0],
        forecast_day_2=forecast[1],
        forecast_day_3=forecast[2],
        forecast_day_4=forecast[3],
        forecast_day_5=forecast[4],
        signal=signal,
        confidence=confidence,
        model_version=model_version,
    )

    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    return prediction