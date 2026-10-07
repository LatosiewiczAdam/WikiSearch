const BASE = "/api";

export interface SearchResult {
  text: string;
  path: string;
  score: number;
}

export interface ChatResponse {
  answer: string;
  sources: string[];
}

export interface SyncStatus {
  status: "idle" | "running" | "done" | "error";
  progress: number;
  total: number;
  message: string;
}

export interface Wiki {
  id: string;
  name: string;
  type: string;
}

export async function fetchWikis(): Promise<Wiki[]> {
  const r = await fetch(`${BASE}/wikis`);
  const d = await r.json();
  if (!r.ok) throw new Error(d.detail ?? "Błąd pobierania wiki");
  return d.wikis;
}

export async function startSync(wikiId: string, clear: boolean): Promise<void> {
  const r = await fetch(`${BASE}/sync`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ wiki_id: wikiId, clear }),
  });
  const d = await r.json();
  if (!r.ok) throw new Error(d.detail ?? "Błąd synchronizacji");
}

export async function getSyncStatus(): Promise<SyncStatus> {
  const r = await fetch(`${BASE}/sync/status`);
  return r.json();
}

export async function semanticSearch(query: string, topK = 6): Promise<SearchResult[]> {
  const r = await fetch(`${BASE}/search?q=${encodeURIComponent(query)}&top_k=${topK}`);
  const d = await r.json();
  if (!r.ok) throw new Error(d.detail ?? "Błąd wyszukiwania");
  return d.results;
}

export async function chat(
  question: string,
  provider: string,
  model: string,
  topK = 6
): Promise<ChatResponse> {
  const r = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, provider, model, top_k: topK }),
  });
  const d = await r.json();
  if (!r.ok) throw new Error(d.detail ?? "Błąd chat");
  return d;
}

export async function fetchModels(provider: string): Promise<string[]> {
  const r = await fetch(`${BASE}/models?provider=${provider}`);
  const d = await r.json();
  if (!r.ok) return [];
  return d.models;
}

export async function fetchStats(): Promise<{ indexed_chunks: number }> {
  const r = await fetch(`${BASE}/stats`);
  return r.json();
}
