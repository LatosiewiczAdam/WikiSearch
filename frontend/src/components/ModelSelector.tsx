import { useEffect, useState } from "react";
import { fetchModels } from "../api";

interface Props {
  provider: string;
  model: string;
  onProviderChange: (p: string) => void;
  onModelChange: (m: string) => void;
}

const PROVIDERS = [
  { value: "ollama", label: "Ollama (lokalny)" },
  { value: "claude", label: "Claude (Anthropic)" },
];

export default function ModelSelector({ provider, model, onProviderChange, onModelChange }: Props) {
  const [models, setModels] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchModels(provider)
      .then((list) => {
        setModels(list);
        if (list.length > 0 && !list.includes(model)) onModelChange(list[0]);
      })
      .finally(() => setLoading(false));
  }, [provider]);

  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
      <select
        value={provider}
        onChange={(e) => onProviderChange(e.target.value)}
        style={selectStyle}
      >
        {PROVIDERS.map((p) => (
          <option key={p.value} value={p.value}>{p.label}</option>
        ))}
      </select>

      <select
        value={model}
        onChange={(e) => onModelChange(e.target.value)}
        disabled={loading || models.length === 0}
        style={selectStyle}
      >
        {models.length === 0 && <option value="">— brak modeli —</option>}
        {models.map((m) => (
          <option key={m} value={m}>{m}</option>
        ))}
      </select>
    </div>
  );
}

const selectStyle: React.CSSProperties = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  color: "var(--text)",
  borderRadius: "var(--radius)",
  padding: "6px 10px",
  fontSize: 13,
  minWidth: 160,
};
