from abc import ABC, abstractmethod
import httpx
import anthropic
from config import settings

SYSTEM_PROMPT = """Jesteś asystentem technicznym pomagającym w odnajdywaniu informacji w dokumentacji DevOps Wiki.
Odpowiadaj wyłącznie na podstawie dostarczonych fragmentów dokumentacji.
Jeśli informacja nie znajduje się w dokumentacji — powiedz to wprost.
Cytuj ścieżki stron wiki gdy odnosisz się do konkretnych informacji.
Odpowiadaj w tym samym języku w którym zadano pytanie."""


class LLMAdapter(ABC):
    @abstractmethod
    async def chat(self, question: str, context_chunks: list[dict]) -> str:
        pass

    @abstractmethod
    async def list_models(self) -> list[str]:
        pass

    def _build_context(self, chunks: list[dict]) -> str:
        parts = []
        for c in chunks:
            parts.append(f"[Strona: {c['path']}]\n{c['text']}")
        return "\n\n---\n\n".join(parts)


class ClaudeAdapter(LLMAdapter):
    def __init__(self, model: str = "claude-sonnet-4-6"):
        self.model = model
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def chat(self, question: str, context_chunks: list[dict]) -> str:
        context = self._build_context(context_chunks)
        message = await self._client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Fragmenty dokumentacji:\n\n{context}\n\n---\n\nPytanie: {question}",
                }
            ],
        )
        return message.content[0].text

    async def list_models(self) -> list[str]:
        return ["claude-sonnet-4-6", "claude-haiku-4-5-20251001", "claude-opus-4-8"]


class OllamaAdapter(LLMAdapter):
    def __init__(self, model: str = "phi3.5"):
        self.model = model

    async def chat(self, question: str, context_chunks: list[dict]) -> str:
        context = self._build_context(context_chunks)
        prompt = f"{SYSTEM_PROMPT}\n\nFragmenty dokumentacji:\n\n{context}\n\n---\n\nPytanie: {question}"

        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=300,
            )
            r.raise_for_status()
            return r.json()["response"]

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{settings.ollama_base_url}/api/tags", timeout=5)
                r.raise_for_status()
                return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []


def get_adapter(provider: str, model: str) -> LLMAdapter:
    if provider == "claude":
        return ClaudeAdapter(model=model)
    if provider == "ollama":
        return OllamaAdapter(model=model)
    raise ValueError(f"Nieznany provider: {provider}")
