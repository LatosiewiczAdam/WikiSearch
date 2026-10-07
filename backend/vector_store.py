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


async def search(query: str, top_k: int = 6) -> list[dict]:
    """Szuka semantycznie w ChromaDB."""
    q_embed = await embed([query])
    results = _collection.query(query_embeddings=q_embed, n_results=top_k, include=["documents", "metadatas", "distances"])

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        hits.append({"text": doc, "path": meta["path"], "score": round(1 - dist, 3)})
    return hits


def get_stats() -> dict:
    return {"indexed_chunks": _collection.count()}


def clear_index() -> None:
    _client.delete_collection("wiki_pages")
    global _collection
    _collection = _client.get_or_create_collection(
        name="wiki_pages",
        metadata={"hnsw:space": "cosine"},
    )
