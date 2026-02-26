
import google.generativeai as genai
from app.core.config import settings


class GeminiLLM:

    def __init__(self):
        api_key = settings.GEMINI_API_KEY

        if not api_key:
            raise ValueError("GEMINI_API_KEY not set")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite")

    def generate(self, prompt: str):

        response = self.model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 800,
            }
        )

        return response.text



_llm_instance = None


def get_llm():
    global _llm_instance

    if _llm_instance is None:
        _llm_instance = GeminiLLM()

    return _llm_instance