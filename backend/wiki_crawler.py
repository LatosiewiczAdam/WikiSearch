import base64
import re
from typing import Any
import httpx
from config import settings

_BASE = f"https://dev.azure.com/{settings.azure_devops_org}/{settings.azure_devops_project}/_apis"
_HEADERS = {
    "Authorization": "Basic " + base64.b64encode(f":{settings.azure_devops_pat}".encode()).decode(),
    "Content-Type": "application/json",
}
_API_VER = "api-version=7.1"


async def _get(client: httpx.AsyncClient, url: str) -> Any:
    r = await client.get(url, headers=_HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


async def get_wikis() -> list[dict]:
    async with httpx.AsyncClient() as client:
        data = await _get(client, f"{_BASE}/wiki/wikis?{_API_VER}")
    return data.get("value", [])


async def get_all_pages(wiki_id: str) -> list[dict]:
    """Pobiera wszystkie strony wiki rekurencyjnie."""
    async with httpx.AsyncClient() as client:
        data = await _get(
            client,
            f"{_BASE}/wiki/wikis/{wiki_id}/pages?path=/&recursionLevel=full&includeContent=false&{_API_VER}",
        )

    pages = []
    _collect_pages(data, pages)
    return pages


def _collect_pages(node: dict, result: list) -> None:
    if not node:
        return
    if node.get("path") and node.get("path") != "/":
        result.append({"id": node.get("id"), "path": node.get("path"), "order": node.get("order", 0)})
    for child in node.get("subPages", []):
        _collect_pages(child, result)


async def get_page_content(wiki_id: str, path: str) -> str:
    """Pobiera treść strony jako Markdown."""
    async with httpx.AsyncClient() as client:
        encoded = path.replace(" ", "%20")
        r = await client.get(
            f"{_BASE}/wiki/wikis/{wiki_id}/pages?path={encoded}&includeContent=true&{_API_VER}",
            headers=_HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
    return data.get("content", "")


def chunk_text(text: str, path: str, chunk_size: int = 800, overlap: int = 100) -> list[dict]:
    """Dzieli tekst na chunki z zachowaniem metadanych."""
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []

    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append({"text": chunk, "path": path, "chunk_index": len(chunks)})
        if end == len(words):
            break
        start = end - overlap

    return chunks
