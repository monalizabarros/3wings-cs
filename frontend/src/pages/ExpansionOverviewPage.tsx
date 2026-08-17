import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import StatusBadge from "../components/StatusBadge";
import {
  EXPANSION_STAGE_LABELS,
  EXPANSION_STAGE_TONE,
  EXPANSION_TYPE_LABELS,
  type ExpansionOpportunityWithClient,
} from "../types";

export default function ExpansionOverviewPage() {
  const [items, setItems] = useState<ExpansionOpportunityWithClient[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<ExpansionOpportunityWithClient[]>("/expansion-opportunities")
      .then(setItems)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Erro ao carregar oportunidades."));
  }, []);

  const totalEstimated = items?.reduce((sum, o) => sum + (o.estimated_value ?? 0), 0) ?? 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <h1 style={{ fontSize: 20, color: "var(--color-graphite)" }}>Expansão</h1>
      <div style={{ fontSize: 12.5, color: "var(--text-muted)" }}>
        Oportunidades de cross-sell e upsell em aberto, em todas as contas. Valor estimado total: R$ {totalEstimated.toLocaleString("pt-BR")}.
      </div>

      {error && <div style={{ fontSize: 13, color: "var(--color-danger-text)" }}>{error}</div>}

      <div style={{ background: "var(--surface-card)", border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-card)", overflow: "hidden" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1.2fr 0.8fr 2fr 1fr 1fr", padding: "10px 16px", fontSize: 11.5, color: "var(--text-muted)", borderBottom: "0.5px solid var(--border-subtle)", letterSpacing: "0.03em" }}>
          <div>CLIENTE</div>
          <div>TIPO</div>
          <div>DESCRIÇÃO</div>
          <div>VALOR ESTIMADO</div>
          <div>ESTÁGIO</div>
        </div>
        {items === null && <div style={{ padding: 16, fontSize: 13, color: "var(--text-muted)" }}>Carregando...</div>}
        {items?.length === 0 && <div style={{ padding: 16, fontSize: 13, color: "var(--text-muted)" }}>Nenhuma oportunidade em aberto no momento.</div>}
        {items?.map((opp) => (
          <div key={opp.id} style={{ display: "grid", gridTemplateColumns: "1.2fr 0.8fr 2fr 1fr 1fr", alignItems: "center", padding: "11px 16px", fontSize: 13, borderBottom: "0.5px solid var(--border-subtle)" }}>
            <Link to={`/clientes/${opp.client_id}`} style={{ color: "var(--color-blue)", fontWeight: 500 }}>
              {opp.client_name}
            </Link>
            <div style={{ color: "var(--text-secondary)" }}>{EXPANSION_TYPE_LABELS[opp.type]}</div>
            <div style={{ color: "var(--text-secondary)" }}>{opp.description}</div>
            <div style={{ color: "var(--text-secondary)" }}>{opp.estimated_value != null ? `R$ ${opp.estimated_value.toLocaleString("pt-BR")}` : "—"}</div>
            <div>
              <StatusBadge label={EXPANSION_STAGE_LABELS[opp.stage]} tone={EXPANSION_STAGE_TONE[opp.stage]} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
