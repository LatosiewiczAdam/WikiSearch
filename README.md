# WikiSearch

Semantyczne wyszukiwanie po stronach Azure DevOps Wiki z możliwością zadawania pytań w języku naturalnym. Backend indeksuje dokumentację w lokalnej bazie wektorowej (ChromaDB), a odpowiedzi generuje lokalny model Ollama lub Claude (opcjonalnie).

```
┌─────────────────┐     REST API      ┌──────────────────────┐
│  React + Vite   │ ◄───────────────► │  FastAPI + ChromaDB  │
│  localhost:5173 │                   │  localhost:8000       │
└─────────────────┘                   └──────────┬───────────┘
                                                  │
                                       ┌──────────▼───────────┐
                                       │  Ollama (lokalnie)   │
                                       │  embeddingi + chat   │
                                       └──────────────────────┘
```

---

## Wymagania

| Narzędzie | Minimalna wersja | Opis |
|-----------|-----------------|------|
| Python | 3.10+ | backend |
| Node.js | 18+ | frontend |
| [Ollama](https://ollama.com) | najnowsza | lokalne LLM i embeddingi |
| Azure DevOps PAT | — | dostęp do odczytu Wiki |

### Modele Ollama

Przed pierwszym uruchomieniem pobierz wymagane modele:

```bash
# model embeddingów (wymagany)
ollama pull nomic-embed-text

# model do chatu (domyślny, ~2GB)
ollama pull llama3.2:3b
```

---

## Konfiguracja

Skopiuj plik przykładowy i uzupełnij dane:

```bash
cp backend/.env.example backend/.env
```

Edytuj `backend/.env`:

```env
# Azure DevOps — PAT musi mieć uprawnienie "Wiki (Read)"
AZURE_DEVOPS_PAT=twoj_personal_access_token
AZURE_DEVOPS_ORG=nazwa_organizacji       # np. "contoso"
AZURE_DEVOPS_PROJECT=nazwa_projektu      # np. "MyProject"

# Ollama (domyślne wartości działają przy lokalnej instalacji)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text

# Opcjonalnie — tylko jeśli chcesz używać Claude zamiast Ollama
# ANTHROPIC_API_KEY=sk-ant-...
```

> **Jak zdobyć PAT**: Azure DevOps → User Settings → Personal Access Tokens → New Token → zakres `Wiki (Read)`.

---

## Uruchomienie

### Windows (zalecane)

```powershell
.\start.ps1
```

Skrypt automatycznie tworzy virtualenv Pythona, instaluje zależności i startuje oba procesy w osobnych oknach.

### Ręcznie

**Backend:**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Aplikacja dostępna pod: **http://localhost:5173**  
API (Swagger UI): **http://localhost:8000/docs**

---

## Pierwsze użycie

1. Upewnij się, że Ollama działa (`ollama serve` lub jako usługa systemowa).
2. Otwórz aplikację w przeglądarce.
3. Przejdź do zakładki **Sync** i uruchom synchronizację Wiki — strony zostaną pobrane i zaindeksowane lokalnie.
4. Po zakończeniu synchronizacji możesz wyszukiwać semantycznie lub zadawać pytania w czacie.

---

## Stos technologiczny

**Backend**
- FastAPI + Uvicorn
- ChromaDB (lokalna baza wektorowa)
- Ollama (embeddingi: `nomic-embed-text`, chat: `llama3.2`)
- Anthropic SDK (opcjonalny provider Claude)

**Frontend**
- React 18 + TypeScript
- Vite
- react-markdown
