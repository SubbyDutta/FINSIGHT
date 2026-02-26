from pydantic import BaseModel
from datetime import datetime


class ArticleOut(BaseModel):
    title: str
    description: str | None
    url: str
    source: str | None
    published_at: datetime | None

    class Config:
        from_attributes = True