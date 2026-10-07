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


def strip_markdown(text: str) -> str:
    text = re.sub(r"^```[^\n]*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^~~~[^\n]*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^#{1,6}\s+(.+)$", r"\1", text, flags=re.MULTILINE)
    text = re.sub(r"^[-=]{3,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    return text


def chunk_text(text: str, path: str, chunk_size: int = 1500, overlap: int = 1) -> list[dict]:
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return []

    heading_pattern = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)

    current_heading = ""
    para_data = []
    for para in text.split("\n\n"):
        m = heading_pattern.search(para)
        if m:
            current_heading = m.group(1).strip()
        cleaned = strip_markdown(para).strip()
        if cleaned:
            para_data.append((cleaned, current_heading))

    if not para_data:
        return []

    chunks = []
    start = 0

    while start < len(para_data):
        chunk_paras = []
        chunk_heading = para_data[start][1]
        size = 0
        i = start

        while i < len(para_data):
            para_text, _ = para_data[i]
            extra = 2 if size > 0 else 0
            if size == 0 or size + extra + len(para_text) <= chunk_size:
                chunk_paras.append(para_text)
                size += extra + len(para_text)
                i += 1
            else:
                break

        if not chunk_paras:
            para_text, para_heading = para_data[start]
            sentences = para_text.split(". ")
            current = ""
            for s in sentences:
                candidate = current + (". " if current else "") + s
                if not current or len(candidate) <= chunk_size:
                    current = candidate
                else:
                    chunks.append({"text": current, "path": path, "chunk_index": len(chunks), "heading": para_heading})
                    current = s
            if current:
                chunks.append({"text": current, "path": path, "chunk_index": len(chunks), "heading": para_heading})
            start += 1
            continue

        chunks.append({
            "text": "\n\n".join(chunk_paras),
            "path": path,
            "chunk_index": len(chunks),
            "heading": chunk_heading,
        })
        start = max(i - overlap, start + 1)

    return chunks
