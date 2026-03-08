from __future__ import annotations

import math
import re
import time
from datetime import datetime, timezone
from typing import Any

from app.api.ai.llm import get_llm
from app.api.ai.vector_store import (
    search_policy_chunks,
    search_similar_scoped,
    upsert_news_documents,
)

from app.services.news_service import fetch_stored_news
from app.services.rag_policy_service import ensure_policy_pdfs_indexed
from app.services.sentiment_service import get_sentiment_summary
from app.services.stock_service import get_stock_quote, normalize_ticker


MIN_Q_LEN = 3
MAX_Q_LEN = 1200
TOP_K = 3
MAX_TOP_K = 5

POLICY_TERMS = {
    "policy","policies","compliance","governance",
    "risk","privacy","regulation","internal control"
}

INTERNAL_POLICY = """
FinSight Internal RAG Policy:
1) Only use retrieved context as evidence
2) If evidence missing say so
3) Never invent numbers or events
4) Cite sources [1] [2]
5) Avoid giving financial advice
""".strip()


def clean(x: Any) -> str:
    return "" if x is None else str(x).strip()


def tokenize(text: str):
    return set(re.findall(r"[a-zA-Z0-9]+", text.lower()))


def lexical_overlap(q: str, doc: str) -> float:
    q_tokens = tokenize(q)
    if not q_tokens:
        return 0

    d_tokens = tokenize(doc)
    return len(q_tokens & d_tokens) / len(q_tokens)


def recency_bonus(published_at):
    if not published_at:
        return 0

    if isinstance(published_at, str):
        if published_at.endswith("Z"):
            published_at = published_at.replace("Z","+00:00")
        try:
            published_at = datetime.fromisoformat(published_at)
        except:
            return 0

    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)

    days = max((datetime.now(timezone.utc) - published_at).days,0)
    return math.exp(-days/30)


def build_context(question, hits, top_k):

    merged = {}

    for h in hits:
        doc_id = clean(h.get("id"))
        if not doc_id:
            continue

        old = merged.get(doc_id)
        if not old or (h.get("distance",1) < old.get("distance",1)):
            merged[doc_id] = h

    ranked = []

    for h in merged.values():

        doc = clean(h.get("document"))
        meta = h.get("metadata",{})

        semantic = 1/(1+max(h.get("distance",0),0))
        lexical = lexical_overlap(question, doc)
        fresh = recency_bonus(meta.get("published_at"))

        score = 0.7*semantic + 0.25*lexical + 0.05*fresh
        h["score"] = score

        ranked.append(h)

    ranked.sort(key=lambda x: x["score"], reverse=True)
    ranked = ranked[:top_k]

    context_lines = []
    sources = []

    for i,h in enumerate(ranked,1):

        meta = h.get("metadata",{})
        doc = clean(h.get("document"))[:320]

        title = clean(meta.get("title")) or "Untitled"

        block = f"""
[{i}] Title: {title}
Source: {clean(meta.get("source"))}
Published: {clean(meta.get("published_at"))}
URL: {clean(meta.get("url"))}
Content: {doc}
""".strip()

        context_lines.append(block)

        sources.append({
            "rank": i,
            "title": title,
            "url": clean(meta.get("url")),
            "content": doc
        })

    return "\n\n".join(context_lines), sources



def build_prompt(ticker, question, stock, sentiment, context):

    return f"""
You are FinSight AI's financial research assistant.

{INTERNAL_POLICY}

Stock
Ticker: {ticker}
Price: {stock.get("price")}
Change: {stock.get("change")} ({stock.get("change_percent")}%)

Sentiment
{sentiment}

Context
{context}

Question
{question}

Instructions
- Use only provided context
- Cite [1] [2]
- If context insufficient say:
"Insufficient grounded evidence from retrieved news context."
""".strip()



def generate_explanation(db, ticker, question, top_k=TOP_K):

    start = time.perf_counter()

    question = clean(question)

    if len(question) < MIN_Q_LEN:
        raise ValueError("Question too short")

    if len(question) > MAX_Q_LEN:
        raise ValueError("Question too long")

    ticker = normalize_ticker(clean(ticker))
    top_k = max(1, min(top_k, MAX_TOP_K))

    
    stock = get_stock_quote(ticker)
    sentiment = get_sentiment_summary(db, ticker)

    
    articles = fetch_stored_news(db, ticker)

    articles = [{
        "article_id": a.id,
        "title": clean(a.title),
        "description": clean(a.description),
        "url": clean(a.url),
        "source": clean(a.source),
        "published_at": a.published_at
    } for a in articles][:50]

    indexed = upsert_news_documents(ticker, articles)

    
    queries = [question, f"{ticker} {question}"]

    hits = []

    for q in queries:
        hits += search_similar_scoped(q, ticker, n_results=6)

    
    if any(t in question.lower() for t in POLICY_TERMS):
        ensure_policy_pdfs_indexed()
        hits += search_policy_chunks(question, n_results=2)

    context, sources = build_context(question, hits, top_k)

    if not sources:
        answer = "Insufficient grounded evidence from retrieved news context."

    else:

        llm = get_llm()

        prompt = build_prompt(
            ticker,
            question,
            stock,
            sentiment.get("message",""),
            context
        )

        response = llm.invoke(prompt)
        answer = getattr(response,"content",str(response))

    latency = int((time.perf_counter()-start)*1000)

    return {
        "answer": answer,
        "sources": [s["content"] for s in sources],
        "ticker": ticker,
        "grounded": bool(sources),
        "retrieval_stats":{
            "candidate_articles": len(articles),
            "indexed_documents": indexed,
            "used_sources": len(sources),
            "latency_ms": latency
        }
    }