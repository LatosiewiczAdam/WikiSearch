import { useEffect, useState } from "react";
import { fetchWikis, fetchStats, getSyncStatus, startSync, Wiki, SyncStatus } from "../api";

export default function SyncPanel() {
  const [wikis, setWikis] = useState<Wiki[]>([]);
  const [selectedWiki, setSelectedWiki] = useState("");
  const [status, setStatus] = useState<SyncStatus>({ status: "idle", progress: 0, total: 0, message: "" });
  const [stats, setStats] = useState<{ indexed_chunks: number } | null>(null);
  const [error, setError] = useState("");
  const [clearOnSync, setClearOnSync] = useState(false);

  useEffect(() => {
    fetchWikis()
      .then((list) => {
        setWikis(list);
        if (list.length > 0) setSelectedWiki(list[0].id);
      })
      .catch((e) => setError(e.message));

    fetchStats().then(setStats).catch(() => {});
    getSyncStatus().then(setStatus).catch(() => {});
  }, []);

  useEffect(() => {
    if (status.status !== "running") return;
    const id = setInterval(async () => {
      const s = await getSyncStatus();
      setStatus(s);
      if (s.status !== "running") {
        clearInterval(id);
        fetchStats().then(setStats);
      }
    }, 1500);
    return () => clearInterval(id);
  }, [status.status]);

  const handleSync = async () => {
    setError("");
    try {
      await startSync(selectedWiki, clearOnSync);
      setStatus({ status: "running", progress: 0, total: 0, message: "Uruchamianie..." });
    } catch (e: any) {
      setError(e.message);
    }
  };

  const pct = status.total > 0 ? Math.round((status.progress / status.total) * 100) : 0;

  return (
    <div style={panelStyle}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <span style={{ fontWeight: 600, fontSize: 13 }}>Synchronizacja Wiki</span>
        {stats && (
          <span style={{ color: "var(--text-muted)", fontSize: 12 }}>
            {stats.indexed_chunks} chunków w indeksie
          </span>
        )}
      </div>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        <select
          value={selectedWiki}
          onChange={(e) => setSelectedWiki(e.target.value)}
          style={selectStyle}
        >
          {wikis.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
          {wikis.length === 0 && <option value="">— brak wiki —</option>}
        </select>

        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--text-muted)", cursor: "pointer" }}>
          <input type="checkbox" checked={clearOnSync} onChange={(e) => setClearOnSync(e.target.checked)} />
          Wyczyść przed synchronizacją
        </label>

        <button
          onClick={handleSync}
          disabled={status.status === "running" || !selectedWiki}
          style={btnStyle}
        >
          {status.status === "running" ? "Synchronizuję..." : "Synchronizuj"}
        </button>
      </div>

      {status.message && (
        <div style={{ marginTop: 10 }}>
          {status.status === "running" && (
            <div style={{ background: "var(--bg)", borderRadius: 6, height: 6, overflow: "hidden", marginBottom: 6 }}>
              <div style={{ background: "var(--accent)", width: `${pct}%`, height: "100%", transition: "width 0.4s" }} />
            </div>
          )}
          <span style={{ fontSize: 12, color: status.status === "error" ? "var(--error)" : status.status === "done" ? "var(--success)" : "var(--text-muted)" }}>
            {status.message}
          </span>
        </div>
      )}

      {error && <div style={{ marginTop: 8, fontSize: 12, color: "var(--error)" }}>{error}</div>}
    </div>
  );
}

const panelStyle: React.CSSProperties = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius)",
  padding: "14px 16px",
  marginBottom: 20,
};

const selectStyle: React.CSSProperties = {
  background: "var(--bg)",
  border: "1px solid var(--border)",
  color: "var(--text)",
  borderRadius: "var(--radius)",
  padding: "6px 10px",
  fontSize: 13,
};

const btnStyle: React.CSSProperties = {
  background: "var(--accent)",
  color: "#fff",
  borderRadius: "var(--radius)",
  padding: "6px 16px",
  fontSize: 13,
  fontWeight: 600,
  opacity: 1,
};
