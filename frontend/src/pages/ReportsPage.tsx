import { useState, type CSSProperties } from "react";
import { downloadFile, ApiError } from "../api/client";

const REPORTS = [
  { key: "carteira", label: "Carteira de clientes", dateHint: "Filtra por início do relacionamento" },
  { key: "health-score", label: "Health Score", dateHint: "Filtra pela data do cálculo mais recente" },
  { key: "satisfacao", label: "Satisfação (NPS/CSAT)", dateHint: "Filtra pela data da resposta" },
  { key: "onboarding", label: "Onboarding e adoção", dateHint: "Filtra pelo início da jornada" },
  { key: "utilizacao", label: "Utilização de módulos", dateHint: "Filtra pela data de contratação do módulo" },
];

export default function ReportsPage() {
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  async function handleDownload(key: string) {
    setDownloading(key);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (startDate) params.set("start_date", startDate);
      if (endDate) params.set("end_date", endDate);
      const query = params.toString() ? `?${params}` : "";
      await downloadFile(`/reports/${key}.csv${query}`, `${key}.csv`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao exportar relatório.");
    } finally {
      setDownloading(null);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <h1 style={{ fontSize: 20, color: "var(--color-graphite)" }}>Relatórios</h1>
      <div style={{ fontSize: 12.5, color: "var(--text-muted)" }}>Exportação em CSV, compatível com Excel.</div>

      <div style={{ display: "flex", gap: 16, alignItems: "flex-end", background: "var(--surface-card)", border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-card)", padding: "14px 18px" }}>
        <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>
          Data inicial
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} style={fieldInput} />
        </label>
        <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>
          Data final
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} style={fieldInput} />
        </label>
        {(startDate || endDate) && (
          <button
            onClick={() => {
              setStartDate("");
              setEndDate("");
            }}
            style={{ background: "transparent", border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-control)", padding: "7px 12px", fontSize: 12.5, color: "var(--text-secondary)" }}
          >
            Limpar período
          </button>
        )}
        <div style={{ fontSize: 11.5, color: "var(--text-muted)" }}>
          Deixe em branco para exportar tudo. Cada relatório usa a data mais relevante para si (veja abaixo).
        </div>
      </div>

      {error && <div style={{ fontSize: 13, color: "var(--color-danger-text)" }}>{error}</div>}

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {REPORTS.map((r) => (
          <div key={r.key} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", background: "var(--surface-card)", border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-card)", padding: "14px 18px" }}>
            <div>
              <div style={{ fontSize: 14, color: "var(--color-graphite)" }}>{r.label}</div>
              <div style={{ fontSize: 11.5, color: "var(--text-muted)" }}>{r.dateHint}</div>
            </div>
            <button
              onClick={() => handleDownload(r.key)}
              disabled={downloading === r.key}
              style={{ background: "var(--color-blue)", color: "#fff", border: "none", borderRadius: "var(--radius-control)", padding: "7px 14px", fontSize: 13, fontWeight: 500 }}
            >
              {downloading === r.key ? "Baixando..." : "Baixar CSV"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

const fieldInput: CSSProperties = {
  display: "block",
  marginTop: 4,
  padding: "6px 8px",
  borderRadius: "var(--radius-control)",
  border: "0.5px solid var(--border-default)",
  fontSize: 13,
};
