import json
import os
from contextlib import contextmanager
from datetime import datetime

from langchain.agents import create_agent

import app.api.ai.agent_tools as agent_tools_module
from app.api.ai.agent_tools import (
    fetch_stock_price,
    get_price_prediction_tool,
    get_recent_news_tool,
    get_sentiment_summary_tool,
    get_technical_analysis_tool,
)
from app.api.ai.llm import get_llm
from app.integrations.pdf_generator import generate_pdf_report
from app.schemas.research_report_schema import ResearchReport
from app.services.lstm_inference_service import predict_ticker
from app.services.news_service import fetch_stored_news
from app.services.ohlcv_service import get_latest_indicators
from app.services.sentiment_service import get_sentiment_summary


TOOLS = [
    fetch_stock_price,
    get_sentiment_summary_tool,
    get_price_prediction_tool,
    get_recent_news_tool,
    get_technical_analysis_tool,
]


SYSTEM_PROMPT = """
You are a professional financial research analyst.

You MUST use the available tools to gather:
- stock price
- sentiment summary
- LSTM prediction
- technical indicators
- recent news

Rules:
- Use only tool outputs as evidence.
- Do not invent facts or values.
- If data is missing, state it explicitly.
- Return ONLY valid JSON.

JSON format:
{
  "summary": "...",
  "news_highlights": ["..."],
  "risk_factors": ["..."],
  "recommendation": "BUY | HOLD | SELL with one-line reason",
  "analyst_note": "..."
}
"""


@contextmanager
def _bind_tool_dependencies(db):
    original_get_sentiment_summary = agent_tools_module.get_sentiment_summary
    original_predict_ticker = agent_tools_module.predict_ticker
    original_get_articles = agent_tools_module.get_articles
    original_get_latest_indicators = agent_tools_module.get_latest_indicators

    def _sentiment_adapter(ticker: str):
        payload = get_sentiment_summary(db, ticker)
        if not isinstance(payload, dict):
            return {"label": "Neutral", "score": 0.0, "article_count": 0}

        counts = payload.get("counts", {})
        article_count = sum(counts.values()) if isinstance(counts, dict) else 0
        return {
            "label": payload.get("interpretation", "Neutral"),
            "score": float(payload.get("sentiment_score", 0.0)),
            "article_count": int(article_count),
        }

    def _prediction_adapter(ticker: str):
        return predict_ticker(db, ticker)

    def _news_adapter(ticker: str):
        articles = fetch_stored_news(db, ticker)
        return [{"title": getattr(article, "title", "")} for article in articles]

    def _technical_adapter(ticker: str):
        return get_latest_indicators(db, ticker)

    agent_tools_module.get_sentiment_summary = _sentiment_adapter
    agent_tools_module.predict_ticker = _prediction_adapter
    agent_tools_module.get_articles = _news_adapter
    agent_tools_module.get_latest_indicators = _technical_adapter

    try:
        yield
    finally:
        agent_tools_module.get_sentiment_summary = original_get_sentiment_summary
        agent_tools_module.predict_ticker = original_predict_ticker
        agent_tools_module.get_articles = original_get_articles
        agent_tools_module.get_latest_indicators = original_get_latest_indicators


def _extract_json(text: str) -> dict:
    text = (text or "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    if "```" in text:
        cleaned = text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])

    raise ValueError("Agent did not return valid JSON")


def _extract_agent_text(result: dict) -> str:
    if isinstance(result, dict) and "messages" in result:
        messages = result.get("messages", [])
        if messages:
            content = getattr(messages[-1], "content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = []
                for chunk in content:
                    if isinstance(chunk, dict):
                        parts.append(chunk.get("text", ""))
                    else:
                        parts.append(str(chunk))
                return "".join(parts)

    if isinstance(result, dict) and "output" in result:
        return str(result["output"])

    return str(result)


def run_research_agent(db, ticker: str):
    with _bind_tool_dependencies(db):
        agent = create_agent(
            model=get_llm(),
            tools=TOOLS,
            system_prompt=SYSTEM_PROMPT,
        )

        user_prompt = (
            f"Analyze ticker: {ticker}. "
            "Use tools before answering and return only valid JSON."
        )
        result = agent.invoke({"messages": [{"role": "user", "content": user_prompt}]})

    parsed = _extract_json(_extract_agent_text(result))
    return parsed


def generate_research_report(db, ticker: str):
    with _bind_tool_dependencies(db):
        stock = fetch_stock_price.run(ticker)
        sentiment = get_sentiment_summary_tool.run(ticker)
        prediction = get_price_prediction_tool.run(ticker)
        technical = get_technical_analysis_tool.run(ticker)
        news = get_recent_news_tool.run(ticker)

    analysis = run_research_agent(db, ticker)

    trend = "sideways"
    forecast = prediction.get("forecast_5d", [])
    if not forecast:
        forecast = [float(stock["price"])] * 5
    elif len(forecast) < 5:
        forecast = forecast + [forecast[-1]] * (5 - len(forecast))

    if forecast[-1] > forecast[0]:
        trend = "upward"
    elif forecast[-1] < forecast[0]:
        trend = "downward"

    technical_payload = {
        "rsi": technical.get("rsi"),
        "macd_signal": str(technical.get("macd", technical.get("macd_signal", "N/A"))),
        "bb_position": technical.get("bb_position"),
        "overall_signal": technical.get("overall_signal", "HOLD"),
    }

    report = ResearchReport(
        ticker=ticker,
        generated_at=datetime.utcnow(),
        summary=analysis.get("summary", "No summary generated."),
        fundamentals={
            "current_price": stock["price"],
            "change_percent": stock.get("change_percent"),
        },
        sentiment=sentiment,
        prediction={
            "forecast_5d": forecast,
            "trend": trend,
            "confidence": prediction.get("confidence", 0.0),
            "model_version": prediction.get("model_version", "lstm_global_v1"),
        },
        technical=technical_payload,
        news_highlights=analysis.get("news_highlights", news.get("headlines", [])),
        risk_factors=analysis.get("risk_factors", []),
        recommendation=analysis.get("recommendation", "HOLD"),
        analyst_note=analysis.get("analyst_note", ""),
    )

    directory = f"reports/{ticker}"
    os.makedirs(directory, exist_ok=True)

    json_path = f"{directory}/latest_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(mode="json"), f, indent=2)

    pdf_path = generate_pdf_report(report)

    return {
        "report": report,
        "json_path": json_path,
        "pdf_path": pdf_path,
    }
