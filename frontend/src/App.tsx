import { useState } from "react";
import { semanticSearch, SearchResult } from "./api";
import SyncPanel from "./components/SyncPanel";
import SearchResults from "./components/SearchResults";
import ChatPanel from "./components/ChatPanel";

type Tab = "search" | "chat";

export default function App() {
  const [tab, setTab] = useState<Tab>("search");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState("");

  const doSearch = async () => {
    const q = query.trim();
    if (!q) return;
    setSearching(true);
    setError("");
    try {
      const hits = await semanticSearch(q);
      setResults(hits);
      setSearched(true);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div style={{ maxWidth: 860, margin: "0 auto", padding: "32px 16px" }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>DevOps Wiki Search</h1>
        <p style={{ color: "var(--text-muted)", fontSize: 13 }}>
          Semantyczne wyszukiwanie i chat z dokumentacją Azure DevOps Wiki
        </p>
      </div>

      <SyncPanel />

      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: 20, borderBottom: "1px solid var(--border)", paddingBottom: 0 }}>
        {(["search", "chat"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              background: "none",
              color: tab === t ? "var(--accent)" : "var(--text-muted)",
              borderBottom: tab === t ? "2px solid var(--accent)" : "2px solid transparent",
              padding: "8px 16px",
              fontSize: 14,
              fontWeight: tab === t ? 600 : 400,
              marginBottom: -1,
            }}
          >
            {t === "search" ? "Wyszukiwarka" : "Chat AI"}
          </button>
        ))}
      </div>

      {/* Search tab */}
      {tab === "search" && (
        <div>
          <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && doSearch()}
              placeholder="Wyszukaj w dokumentacji..."
              style={inputStyle}
            />
            <button onClick={doSearch} disabled={searching || !query.trim()} style={btnStyle}>
              {searching ? "Szukam..." : "Szukaj"}
            </button>
          </div>

          {error && <div style={{ fontSize: 12, color: "var(--error)", marginBottom: 12 }}>{error}</div>}

          {searched && results.length === 0 && !searching && (
            <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Brak wyników. Upewnij się, że wiki jest zsynchronizowana.</div>
          )}

          <SearchResults results={results} query={query} />
        </div>
      )}

      {/* Chat tab */}
      {tab === "chat" && <ChatPanel />}
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  flex: 1,
  background: "var(--surface)",
  border: "1px solid var(--border)",
  color: "var(--text)",
  borderRadius: "var(--radius)",
  padding: "10px 14px",
  fontSize: 14,
};

const btnStyle: React.CSSProperties = {
  background: "var(--accent)",
  color: "#fff",
  borderRadius: "var(--radius)",
  padding: "10px 22px",
  fontWeight: 600,
  fontSize: 14,
};
