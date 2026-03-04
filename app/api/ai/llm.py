
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings

_llm_instance = None


def get_llm():
    global _llm_instance

    if _llm_instance is None:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set")

        _llm_instance = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0.2,
            max_tokens=800,
            api_key=settings.GEMINI_API_KEY,
        )

    return _llm_instance
