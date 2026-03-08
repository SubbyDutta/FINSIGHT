from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any

import chromadb
from chromadb.config import Settings

from app.api.ai.embeddings import embed_text


client = chromadb.PersistentClient(
    path="./chroma_db",
    settings=Settings(anonymized_telemetry=False),
)
collection = client.get_or_create_collection(name="financial_news")

DEFAULT_CHUNK_SIZE = 900
DEFAULT_CHUNK_OVERLAP = 140


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    metadata = metadata or {}
    normalized: dict[str, Any] = {}
    for key, value in metadata.items():
        if value is None:
            continue
        if isinstance(value, datetime):
            normalized[str(key)] = value.isoformat()
            continue
        if isinstance(value, (str, bool, int, float)):
            normalized[str(key)] = value
            continue
        normalized[str(key)] = str(value)
    return normalized


def _stable_doc_id(ticker: str, source_key: str) -> str:
    seed = f"{ticker}|{source_key}".encode("utf-8")
    digest = hashlib.sha1(seed).hexdigest()
    return f"{ticker}:{digest}"


def _chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP) -> list[str]:
    cleaned = re.sub(r"\s+", " ", _safe_text(text)).strip()
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    safe_overlap = max(0, min(overlap, chunk_size // 2))

    while start < len(cleaned): 
        end = min(start + chunk_size, len(cleaned))
        if end < len(cleaned):
            window_start = start + int(chunk_size * 0.6)
            pivot = cleaned.rfind(" ", window_start, end)
            if pivot > start:
                end = pivot

        piece = cleaned[start:end].strip()
        if piece:
            chunks.append(piece)

        if end >= len(cleaned):
            break
        start = max(0, end - safe_overlap)

    return chunks


def _normalize_hits(raw: dict[str, Any]) -> list[dict[str, Any]]:
    ids = (raw.get("ids") or [[]])[0]
    documents = (raw.get("documents") or [[]])[0]
    metadatas = (raw.get("metadatas") or [[]])[0]
    distances = (raw.get("distances") or [[]])[0]

    hits: list[dict[str, Any]] = []
    for idx, doc_id in enumerate(ids):
        hits.append(
            {
                "id": doc_id, 
                "document": documents[idx] if idx < len(documents) else "",
                "metadata": metadatas[idx] if idx < len(metadatas) and metadatas[idx] else {},
                "distance": distances[idx] if idx < len(distances) else None,
            }
        )
    return hits


def _fetch_existing_ids(ids: list[str]) -> set[str]:
    if not ids:
        return set()
    existing = collection.get(ids=ids, include=["metadatas"])
    existing_ids = existing.get("ids") or []
    return {str(doc_id) for doc_id in existing_ids}


def add_article_embedding(article_id: int, text: str):
    embedding = embed_text(text)
    collection.upsert(
        ids=[str(article_id)],
        documents=[text],
        embeddings=[embedding],
    )


def upsert_news_documents(ticker: str, articles: list[dict[str, Any]]) -> int:
    candidate_docs: list[tuple[str, str, dict[str, Any]]] = []

    seen: set[str] = set()
    for article in articles:
        title = _safe_text(article.get("title"))
        description = _safe_text(article.get("description"))
        content = f"{title}. {description}".strip(". ").strip()
        chunks = _chunk_text(content)
        if not chunks:
            continue

        source_key = _safe_text(article.get("url")) or _safe_text(article.get("article_id"))
        if not source_key:
            source_key = f"{title}|{_safe_text(article.get('published_at'))}"
        total_chunks = len(chunks)
        for chunk_index, chunk in enumerate(chunks):
            doc_id = _stable_doc_id(
                ticker, f"{source_key}|chunk:{chunk_index}|size:{total_chunks}"
            )
            if doc_id in seen:
                continue
            seen.add(doc_id)

            metadata = _normalize_metadata(
                {
                    "ticker": ticker,
                    "title": title,
                    "source": article.get("source"),
                    "url": article.get("url"),
                    "published_at": article.get("published_at"),
                    "doc_type": "news",
                    "chunk_index": chunk_index,
                    "chunk_count": total_chunks,
                    "article_id": article.get("article_id"),
                }
            )

            candidate_docs.append((doc_id, chunk, metadata))

    if not candidate_docs:
        return 0

    existing_ids = _fetch_existing_ids([doc_id for doc_id, _, _ in candidate_docs])

    ids: list[str] = []
    docs: list[str] = []
    embeddings: list[list[float]] = []
    metadatas: list[dict[str, Any]] = []
    for doc_id, chunk, metadata in candidate_docs:
        if doc_id in existing_ids:
            continue
        ids.append(doc_id)
        docs.append(chunk)
        embeddings.append(embed_text(chunk))
        metadatas.append(metadata)

    if not ids:
        return 0

    collection.upsert(
        ids=ids,
        documents=docs,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(ids)


def upsert_policy_document(
    policy_id: str,
    title: str,
    text: str,
    source: str = "internal_policy",
) -> int:
    chunks = _chunk_text(text)
    if not chunks:
        return 0

    ids: list[str] = []
    docs: list[str] = []
    embeddings: list[list[float]] = []
    metadatas: list[dict[str, Any]] = []

    total_chunks = len(chunks)
    for chunk_index, chunk in enumerate(chunks):
        doc_id = _stable_doc_id(
            "__POLICY__", f"{policy_id}|chunk:{chunk_index}|size:{total_chunks}"
        )
        ids.append(doc_id)
        docs.append(chunk)
        embeddings.append(embed_text(chunk))
        metadatas.append(
            _normalize_metadata(
                {
                    "ticker": "__POLICY__",
                    "doc_type": "policy",
                    "policy_id": policy_id,
                    "title": title,
                    "source": source,
                    "chunk_index": chunk_index,
                    "chunk_count": total_chunks,
                }
            )
        )

    collection.upsert(
        ids=ids,
        documents=docs,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(ids)


def search_similar(query: str, n_results: int = 5):
    query_embedding = embed_text(query)
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )


def search_similar_scoped(query: str, ticker: str, n_results: int = 8) -> list[dict[str, Any]]:
    query_embedding = embed_text(query)
    raw = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where={"ticker": ticker},
        include=["documents", "metadatas", "distances"],
    )
    return _normalize_hits(raw)


def search_policy_chunks(query: str, n_results: int = 3) -> list[dict[str, Any]]:
    query_embedding = embed_text(query)
    raw = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where={"doc_type": "policy"},
        include=["documents", "metadatas", "distances"],
    )
    return _normalize_hits(raw)
