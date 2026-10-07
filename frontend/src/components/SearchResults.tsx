import { SearchResult } from "../api";

interface Props {
  results: SearchResult[];
  query: string;
}

export default function SearchResults({ results, query }: Props) {
  if (results.length === 0) return null;

  return (
    <div>
      <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 10 }}>
        {results.length} wyników dla: <strong style={{ color: "var(--text)" }}>{query}</strong>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {results.map((r, i) => (
          <ResultCard key={i} result={r} />
        ))}
      </div>
    </div>
  );
}

function ResultCard({ result }: { result: SearchResult }) {
  const score = Math.round(result.score * 100);
  const color = score >= 80 ? "var(--success)" : score >= 60 ? "var(--accent)" : "var(--text-muted)";

  return (
    <div style={cardStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8, gap: 8 }}>
        <span style={{ fontSize: 12, color: "var(--accent)", fontWeight: 500, wordBreak: "break-word" }}>
          {result.path}
        </span>
        <span style={{ fontSize: 11, color, fontWeight: 600, whiteSpace: "nowrap", background: "var(--bg)", borderRadius: 4, padding: "1px 6px" }}>
          {score}%
        </span>
      </div>
      <p style={{ fontSize: 13, color: "var(--text-muted)", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
        {result.text.slice(0, 400)}{result.text.length > 400 ? "…" : ""}
      </p>
    </div>
  );
}

const cardStyle: React.CSSProperties = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius)",
  padding: "12px 14px",
};
