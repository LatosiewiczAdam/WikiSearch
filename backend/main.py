import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from wiki_crawler import get_wikis, get_all_pages, get_page_content, chunk_text
from vector_store import index_chunks, search, get_stats, clear_index
from llm_adapter import get_adapter


# ---------------------------------------------------------------------------
# Sync state
# ---------------------------------------------------------------------------

_sync_state = {"status": "idle", "progress": 0, "total": 0, "message": ""}


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="DevOps Wiki Search", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    question: str
    provider: str = "ollama"
    model: str = "llama3.2"
    top_k: int = 6
    hybrid: bool = True


class SyncRequest(BaseModel):
    wiki_id: str | None = None
    clear: bool = False


# ---------------------------------------------------------------------------
# Background sync task
# ---------------------------------------------------------------------------

async def _run_sync(wiki_id: str, clear: bool) -> None:
    global _sync_state
    try:
        _sync_state = {"status": "running", "progress": 0, "total": 0, "message": "Pobieranie listy stron..."}

        if clear:
            clear_index()

        pages = await get_all_pages(wiki_id)
        _sync_state["total"] = len(pages)
        _sync_state["message"] = f"Znaleziono {len(pages)} stron. Indeksowanie..."

        total_chunks = 0
        for i, page in enumerate(pages):
            content = await get_page_content(wiki_id, page["path"])
            chunks = chunk_text(content, page["path"])
            if chunks:
                await index_chunks(chunks)
                total_chunks += len(chunks)

            _sync_state["progress"] = i + 1
            _sync_state["message"] = f"Zaindeksowano {i + 1}/{len(pages)} stron ({total_chunks} chunków)"

        _sync_state = {
            "status": "done",
            "progress": len(pages),
            "total": len(pages),
            "message": f"Gotowe. Zaindeksowano {len(pages)} stron, {total_chunks} chunków.",
        }
    except Exception as e:
        _sync_state = {"status": "error", "progress": 0, "total": 0, "message": str(e)}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/wikis")
async def list_wikis():
    try:
        wikis = await get_wikis()
        return {"wikis": wikis}
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/api/sync")
async def sync_wiki(req: SyncRequest, background_tasks: BackgroundTasks):
    if _sync_state["status"] == "running":
        raise HTTPException(status_code=409, detail="Synchronizacja już trwa")

    wikis = await get_wikis()
    if not wikis:
        raise HTTPException(status_code=404, detail="Nie znaleziono żadnego wiki")

    wiki_id = req.wiki_id or wikis[0]["id"]
    background_tasks.add_task(_run_sync, wiki_id, req.clear)
    return {"message": "Synchronizacja uruchomiona", "wiki_id": wiki_id}


@app.get("/api/sync/status")
async def sync_status():
    return _sync_state


@app.get("/api/search")
async def semantic_search(q: str, top_k: int = 6, hybrid: bool = True):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Puste zapytanie")
    try:
        hits = await search(q, top_k=top_k, hybrid=hybrid)
        return {"results": hits, "query": q}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Puste pytanie")
    try:
        hits = await search(req.question, top_k=req.top_k, hybrid=req.hybrid)
        if not hits:
            return {"answer": "Nie znaleziono powiązanej dokumentacji.", "sources": []}

        adapter = get_adapter(req.provider, req.model)
        answer = await adapter.chat(req.question, hits)

        sources = list({h["path"] for h in hits})
        return {"answer": answer, "sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models")
async def list_models(provider: str = "ollama"):
    adapter = get_adapter(provider, "")
    models = await adapter.list_models()
    return {"provider": provider, "models": models}


@app.get("/api/stats")
async def stats():
    return get_stats()


@app.get("/health")
async def health():
    return {"ok": True}
