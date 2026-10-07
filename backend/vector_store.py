import hashlib
import httpx
import chromadb
from chromadb.config import Settings as ChromaSettings
from config import settings

_client = chromadb.PersistentClient(
    path=settings.chroma_persist_dir,
    settings=ChromaSettings(anonymized_telemetry=False),
)
_collection = _client.get_or_create_collection(
    name="wiki_pages",
    metadata={"hnsw:space": "cosine"},
)


async def embed(texts: list[str]) -> list[list[float]]:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{settings.ollama_base_url}/api/embed",
            json={"model": settings.ollama_embed_model, "input": texts},
            timeout=60,
        )
        r.raise_for_status()
        return r.json()["embeddings"]


def _chunk_id(path: str, index: int) -> str:
    return hashlib.md5(f"{path}:{index}".encode()).hexdigest()


async def index_chunks(chunks: list[dict]) -> int:
    """Dodaje chunki do ChromaDB. Zwraca liczbę zaindeksowanych."""
    if not chunks:
        return 0

    texts = [c["text"] for c in chunks]
    embeddings = await embed(texts)

    ids = [_chunk_id(c["path"], c["chunk_index"]) for c in chunks]
    metadatas = [
        {"path": c["path"], "chunk_index": c["chunk_index"], "heading": c.get("heading", "")}
        for c in chunks
    ]

    _collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    return len(chunks)


async def search(query: str, top_k: int = 6, hybrid: bool = True) -> list[dict]:
    """Szuka w ChromaDB — semantycznie lub hybrydowo (BM25 + semantyczne)."""
    q_embed = await embed([query])
    pool_size = min(top_k * 3, 50) if hybrid else top_k
    results = _collection.query(query_embeddings=q_embed, n_results=pool_size, include=["documents", "metadatas", "distances"])

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    if not hybrid:
        return [
            {"text": doc, "path": meta["path"], "score": round(1 - dist, 3)}
            for doc, meta, dist in zip(docs, metas, distances)
        ]

    from rank_bm25 import BM25Okapi

    tokenized = [doc.lower().split() for doc in docs]
    bm25 = BM25Okapi(tokenized)
    bm25_scores = bm25.get_scores(query.lower().split())
    max_bm25 = max(bm25_scores) if len(bm25_scores) > 0 else 0.0

    hits = []
    for doc, meta, dist, bm25_score in zip(docs, metas, distances, bm25_scores):
        semantic_score = 1 - dist
        bm25_norm = bm25_score / (max_bm25 + 1e-9)
        final_score = 0.6 * semantic_score + 0.4 * bm25_norm
        hits.append({"text": doc, "path": meta["path"], "score": round(final_score, 3)})

    hits.sort(key=lambda h: h["score"], reverse=True)
    return hits[:top_k]


def get_stats() -> dict:
    return {"indexed_chunks": _collection.count()}


def clear_index() -> None:
    _client.delete_collection("wiki_pages")
    global _collection
    _collection = _client.get_or_create_collection(
        name="wiki_pages",
        metadata={"hnsw:space": "cosine"},
    )
