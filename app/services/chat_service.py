from app.services.stock_service import get_stock_quote, normalize_ticker
from app.services.sentiment_service import get_sentiment_summary
from app.api.ai.llm import get_llm
from app.api.ai.vector_store import search_similar


def generate_explanation(db, ticker: str, question: str):

    ticker = normalize_ticker(ticker)

    stock = get_stock_quote(ticker)
    sentiment = get_sentiment_summary(db, ticker)

    results = search_similar(question)

    documents = results["documents"][0] if results["documents"] else []

    context = "\n\n".join(documents)

    prompt = f"""
You are a financial research assistant.

Stock: {ticker}
Current price: {stock['price']}
Change: {stock['change']} ({stock['change_percent']}%)

Sentiment summary:
{sentiment}

Relevant News:
{context}

User Question:
{question}

Explain clearly using the news as evidence.
Mention which news points support your reasoning.
Do not hallucinate facts outside the provided context.
"""

    llm = get_llm()

    answer = llm.generate(prompt)

    return answer, documents