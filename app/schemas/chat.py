from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    ticker: str = Field(min_length=1, max_length=15)
    question: str = Field(min_length=3, max_length=1200)
    top_k: int = Field(default=3, ge=1, le=5)

    @field_validator("ticker")
    @classmethod
    def _strip_ticker(cls, value: str) -> str:
        return value.strip()

    @field_validator("question")
    @classmethod
    def _strip_question(cls, value: str) -> str:
        return value.strip()
