from pydantic import BaseModel

class ChatRequest(BaseModel):
    ticker: str
    question: str
