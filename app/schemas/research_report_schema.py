
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class Fundamentals(BaseModel):
    current_price: float
    change_percent: float | None = None


class SentimentSection(BaseModel):
    label: str
    score: float
    article_count: int


class PredictionSection(BaseModel):
    forecast_5d: List[float]
    trend: str
    confidence: float
    model_version: str


class TechnicalSection(BaseModel):
    rsi: float | None = None
    macd_signal: str | None = None
    bb_position: str | None = None
    overall_signal: str


class ResearchReport(BaseModel):
    ticker: str
    generated_at: datetime

    summary: str

    fundamentals: Fundamentals
    sentiment: SentimentSection
    prediction: PredictionSection
    technical: TechnicalSection

    news_highlights: List[str] = Field(default_factory=list)

    risk_factors: List[str] = Field(default_factory=list)

    recommendation: str

    analyst_note: str