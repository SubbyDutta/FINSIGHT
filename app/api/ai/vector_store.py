import chromadb
from chromadb.config import Settings
from app.api.ai.embeddings import embed_text


client =chromadb.Client(
    Settings(
        persist_directory="./chroma_db",
        anonymized_telemetry=False
    )
)

collection = client.get_or_create_collection(name="financial_news")
def add_article_embedding(article_id: int, text: str):
    embedding =embed_text(text)

    collection.add(
        ids=[str(article_id)],
        documents=[text],
        embeddings=[embedding]
    )


def search_similar(query: str, n_results=5):
    query_embedding = embed_text(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    return results