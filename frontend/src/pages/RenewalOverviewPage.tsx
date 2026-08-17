import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import StatusBadge from "../components/StatusBadge";
import {
  CHURN_CATEGORY_LABELS,
  RENEWAL_STATUS_LABELS,
  RENEWAL_STATUS_TONE,
  type ChurnRecord,
  type RenewalWithClient,
} from "../types";

export default function RenewalOverviewPage() {
  const [renewals, setRenewals] = useState<RenewalWithClient[] | null>(null);
  const [churnRecords, setChurnRecords] = useState<ChurnRecord[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<RenewalWithClient[]>("/renewals/upcoming?days=90")
      .then(setRenewals)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Erro ao carregar renovações."));
    api.get<ChurnRecord[]>("/churn-records").then(setChurnRecords).catch(() => setChurnRecords([]));
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <h1 style={{ fontSize: 20, color: "var(--color-graphite)" }}>Renovação</h1>
      <div style={{ fontSize: 12.5, color: "var(--text-muted)" }}>
        Contratos com vencimento nos próximos 90 dias, em todas as contas.
      </div>

      {error && <div style={{ fontSize: 13, color: "var(--color-danger-text)" }}>{error}</div>}

      <div style={{ background: "var(--surface-card)", border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-card)", overflow: "hidden" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr 1fr 1fr", padding: "10px 16px", fontSize: 11.5, color: "var(--text-muted)", borderBottom: "0.5px solid var(--border-subtle)", letterSpacing: "0.03em" }}>
          <div>CLIENTE</div>
          <div>VENCIMENTO</div>
          <div>VALOR</div>
          <div>STATUS</div>
        </div>
        {renewals === null && <div style={{ padding: 16, fontSize: 13, color: "var(--text-muted)" }}>Carregando...</div>}
        {renewals?.length === 0 && <div style={{ padding: 16, fontSize: 13, color: "var(--text-muted)" }}>Nenhuma renovação próxima no momento.</div>}
        {renewals?.map((r) => (
          <div key={r.id} style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr 1fr 1fr", alignItems: "center", padding: "11px 16px", fontSize: 13, borderBottom: "0.5px solid var(--border-subtle)" }}>
            <Link to={`/clientes/${r.client_id}`} style={{ color: "var(--color-blue)", fontWeight: 500 }}>
              {r.client_name}
            </Link>
            <div style={{ color: "var(--text-secondary)" }}>{r.contract_end_date}</div>
            <div style={{ color: "var(--text-secondary)" }}>{r.renewal_value != null ? `R$ ${r.renewal_value.toLocaleString("pt-BR")}` : "—"}</div>
            <div>
              <StatusBadge label={RENEWAL_STATUS_LABELS[r.status]} tone={RENEWAL_STATUS_TONE[r.status]} />
            </div>
          </div>
        ))}
      </div>

      <h2 style={{ fontSize: 16, color: "var(--color-graphite)" }}>Churn registrado</h2>
      <div style={{ background: "var(--surface-card)", border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-card)", overflow: "hidden" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 2fr 1fr", padding: "10px 16px", fontSize: 11.5, color: "var(--text-muted)", borderBottom: "0.5px solid var(--border-subtle)", letterSpacing: "0.03em" }}>
          <div>DATA</div>
          <div>CATEGORIA</div>
          <div>DETALHES</div>
          <div>VALOR PERDIDO</div>
        </div>
        {churnRecords === null && <div style={{ padding: 16, fontSize: 13, color: "var(--text-muted)" }}>Carregando...</div>}
        {churnRecords?.length === 0 && <div style={{ padding: 16, fontSize: 13, color: "var(--text-muted)" }}>Nenhum churn registrado.</div>}
        {churnRecords?.map((c) => (
          <div key={c.id} style={{ display: "grid", gridTemplateColumns: "1fr 1fr 2fr 1fr", alignItems: "center", padding: "11px 16px", fontSize: 13, borderBottom: "0.5px solid var(--border-subtle)" }}>
            <div style={{ color: "var(--text-secondary)" }}>{c.churn_date}</div>
            <div style={{ color: "var(--text-secondary)" }}>{CHURN_CATEGORY_LABELS[c.category]}</div>
            <div style={{ color: "var(--text-secondary)" }}>{c.description || "—"}</div>
            <div style={{ color: "var(--text-secondary)" }}>{c.lost_value != null ? `R$ ${c.lost_value.toLocaleString("pt-BR")}` : "—"}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
