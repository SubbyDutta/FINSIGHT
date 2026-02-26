from pydantic import BaseModel


class SentimentSummary(BaseModel):
    counts: dict
    sentiment_score: float
    interpretation: str