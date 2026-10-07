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

_PARA_SEP = "\n\n"

_RE_CODE_FENCE = re.compile(r"^```[^\n]*", re.MULTILINE)
_RE_TILDE_FENCE = re.compile(r"^~~~[^\n]*", re.MULTILINE)
_RE_HEADING = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
_RE_SEPARATOR = re.compile(r"^[-=]{3,}\s*$", re.MULTILINE)
_RE_BOLD_STAR = re.compile(r"\*\*(.+?)\*\*")
_RE_BOLD_UNDER = re.compile(r"__(.+?)__")
_RE_ITALIC_STAR = re.compile(r"\*(.+?)\*")
_RE_ITALIC_UNDER = re.compile(r"_(.+?)_")
_RE_CODE_INLINE = re.compile(r"`(.+?)`")
_RE_LINK = re.compile(r"\[([^\]]+)\]\([^\)]+\)")


async def _get(client: httpx.AsyncClient, url: str) -> Any:
    r = await client.get(url, headers=_HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


async def get_wikis(client: httpx.AsyncClient) -> list[dict]:
    data = await _get(client, f"{_BASE}/wiki/wikis?{_API_VER}")
    return data.get("value", [])


async def get_all_pages(wiki_id: str, client: httpx.AsyncClient) -> list[dict]:
    """Pobiera wszystkie strony wiki rekurencyjnie."""
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


async def get_page_content(wiki_id: str, path: str, client: httpx.AsyncClient) -> str:
    """Pobiera treść strony jako Markdown."""
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
    text = _RE_CODE_FENCE.sub("", text)
    text = _RE_TILDE_FENCE.sub("", text)
    text = _RE_HEADING.sub(r"\1", text)
    text = _RE_SEPARATOR.sub("", text)
    text = _RE_BOLD_STAR.sub(r"\1", text)
    text = _RE_BOLD_UNDER.sub(r"\1", text)
    text = _RE_ITALIC_STAR.sub(r"\1", text)
    text = _RE_ITALIC_UNDER.sub(r"\1", text)
    text = _RE_CODE_INLINE.sub(r"\1", text)
    text = _RE_LINK.sub(r"\1", text)
    return text


def chunk_text(text: str, path: str, chunk_size: int = 1500, overlap: int = 1) -> list[dict]:
    text = re.sub(r"\n{3,}", _PARA_SEP, text).strip()
    if not text:
        return []

    current_heading = ""
    para_data = []
    for para in text.split(_PARA_SEP):
        m = _RE_HEADING.search(para)
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
            extra = len(_PARA_SEP) if size > 0 else 0
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
            "text": _PARA_SEP.join(chunk_paras),
            "path": path,
            "chunk_index": len(chunks),
            "heading": chunk_heading,
        })
        start = max(i - overlap, start + 1)

    return chunks
