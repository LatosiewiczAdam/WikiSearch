import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { chat } from "../api";
import ModelSelector from "./ModelSelector";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [provider, setProvider] = useState("ollama");
  const [model, setModel] = useState("phi3.5");
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async () => {
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    setError("");
    setMessages((m) => [...m, { role: "user", content: q }]);
    setLoading(true);

    try {
      const res = await chat(q, provider, model);
      setMessages((m) => [...m, { role: "assistant", content: res.answer, sources: res.sources }]);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
        <span style={{ fontWeight: 600, fontSize: 14 }}>Chat z dokumentacją</span>
        <ModelSelector
          provider={provider}
          model={model}
          onProviderChange={setProvider}
          onModelChange={setModel}
        />
      </div>

      {messages.length > 0 && (
        <div style={historyStyle}>
          {messages.map((m, i) => (
            <div key={i} style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: 0.5 }}>
                {m.role === "user" ? "Pytanie" : "Odpowiedź"}
              </div>
              {m.role === "user" ? (
                <div style={{ color: "var(--text)", fontSize: 14 }}>{m.content}</div>
              ) : (
                <div style={markdownStyle}>
                  <ReactMarkdown>{m.content}</ReactMarkdown>
                  {m.sources && m.sources.length > 0 && (
                    <div style={{ marginTop: 10, fontSize: 11, color: "var(--text-muted)" }}>
                      Źródła: {m.sources.map((s, j) => (
                        <span key={j} style={{ marginRight: 8, color: "var(--accent)" }}>{s}</span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div style={{ color: "var(--text-muted)", fontSize: 13, fontStyle: "italic" }}>Generowanie odpowiedzi...</div>
          )}
          <div ref={bottomRef} />
        </div>
      )}

      {error && <div style={{ fontSize: 12, color: "var(--error)" }}>{error}</div>}

      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Zadaj pytanie dotyczące dokumentacji..."
          disabled={loading}
          style={inputStyle}
        />
        <button onClick={send} disabled={loading || !input.trim()} style={btnStyle}>
          Wyślij
        </button>
      </div>
    </div>
  );
}

const historyStyle: React.CSSProperties = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: "var(--radius)",
  padding: "14px 16px",
  maxHeight: 450,
  overflowY: "auto",
};

const markdownStyle: React.CSSProperties = {
  fontSize: 14,
  lineHeight: 1.7,
  color: "var(--text)",
};

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
  padding: "10px 20px",
  fontWeight: 600,
  fontSize: 14,
};
