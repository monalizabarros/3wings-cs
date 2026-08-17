import { useEffect, useState, type CSSProperties, type FormEvent } from "react";
import { api, ApiError } from "../api/client";
import StatusBadge from "./StatusBadge";
import {
  CHURN_CATEGORY_LABELS,
  RENEWAL_STATUS_LABELS,
  RENEWAL_STATUS_TONE,
  type ChurnCategory,
  type Renewal,
} from "../types";

export default function RenewalPanel({ clientId }: { clientId: string }) {
  const [renewals, setRenewals] = useState<Renewal[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  function load() {
    api.get<Renewal[]>(`/clients/${clientId}/renewals`).then(setRenewals).catch(() => setRenewals([]));
  }

  useEffect(load, [clientId]);

  const hasOpenRenewal = renewals?.some((r) => r.status !== "renovado" && r.status !== "nao_renovado") ?? false;

  return (
    <div style={{ background: "var(--surface-card)", border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-card)", padding: "16px 18px", display: "flex", flexDirection: "column", gap: 12 }}>
      {!hasOpenRenewal && (
        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <button onClick={() => setShowForm((v) => !v)} style={primaryButton}>
            {showForm ? "Cancelar" : "+ Novo ciclo de renovação"}
          </button>
        </div>
      )}

      {error && <div style={{ fontSize: 13, color: "var(--color-danger-text)" }}>{error}</div>}

      {showForm && (
        <NewRenewalForm clientId={clientId} onCreated={() => { setShowForm(false); load(); }} onError={setError} />
      )}

      {renewals?.length === 0 && <div style={{ fontSize: 12.5, color: "var(--text-muted)" }}>Nenhum ciclo de renovação registrado ainda.</div>}
      {renewals?.map((r) => (
        <RenewalCard key={r.id} renewal={r} onChanged={load} onError={setError} />
      ))}
    </div>
  );
}

function RenewalCard({ renewal, onChanged, onError }: { renewal: Renewal; onChanged: () => void; onError: (msg: string) => void }) {
  const [completing, setCompleting] = useState<"renewed" | "churn" | null>(null);
  const [nextEndDate, setNextEndDate] = useState("");
  const [churnCategory, setChurnCategory] = useState<ChurnCategory>("preco");
  const [churnDescription, setChurnDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const open = renewal.status !== "renovado" && renewal.status !== "nao_renovado";

  async function complete(renewed: boolean) {
    setSubmitting(true);
    try {
      await api.post(`/renewals/${renewal.id}/complete`, {
        renewed,
        next_contract_end_date: renewed ? nextEndDate || null : null,
        churn_category: renewed ? null : churnCategory,
        churn_description: renewed ? null : churnDescription || null,
      });
      setCompleting(null);
      onChanged();
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Erro ao concluir renovação.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-control)", padding: "12px 14px", display: "flex", flexDirection: "column", gap: 8 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ fontSize: 13, fontWeight: 500, color: "var(--color-graphite)" }}>
          Vencimento do contrato: {renewal.contract_end_date}
        </div>
        <StatusBadge label={RENEWAL_STATUS_LABELS[renewal.status]} tone={RENEWAL_STATUS_TONE[renewal.status]} />
      </div>
      {renewal.renewal_value != null && (
        <div style={{ fontSize: 12.5, color: "var(--text-secondary)" }}>Valor: R$ {renewal.renewal_value.toLocaleString("pt-BR")}</div>
      )}
      {renewal.risk_notes && <div style={{ fontSize: 12.5, color: "var(--text-secondary)" }}>Notas de risco: {renewal.risk_notes}</div>}

      {open && !completing && (
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={() => setCompleting("renewed")} style={{ ...smallButton, borderColor: "var(--color-success-text)", color: "var(--color-success-text)" }}>
            Marcar como renovado
          </button>
          <button onClick={() => setCompleting("churn")} style={{ ...smallButton, borderColor: "var(--color-danger-text)", color: "var(--color-danger-text)" }}>
            Marcar como não renovado
          </button>
        </div>
      )}

      {completing === "renewed" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>
            Nova data de vencimento
            <input type="date" value={nextEndDate} onChange={(e) => setNextEndDate(e.target.value)} style={fieldInput} />
          </label>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={() => complete(true)} disabled={submitting || !nextEndDate} style={primaryButton}>
              {submitting ? "Salvando..." : "Confirmar renovação"}
            </button>
            <button onClick={() => setCompleting(null)} style={smallButton}>Cancelar</button>
          </div>
        </div>
      )}

      {completing === "churn" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>
            Motivo do churn
            <select value={churnCategory} onChange={(e) => setChurnCategory(e.target.value as ChurnCategory)} style={fieldInput}>
              {Object.entries(CHURN_CATEGORY_LABELS).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </label>
          <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>
            Detalhes
            <textarea value={churnDescription} onChange={(e) => setChurnDescription(e.target.value)} style={{ ...fieldInput, minHeight: 40, resize: "vertical", fontFamily: "inherit" }} />
          </label>
          <div style={{ fontSize: 11.5, color: "var(--color-danger-text)" }}>
            Isso vai mudar o status do cliente para Churn e registrar o motivo formalmente.
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={() => complete(false)} disabled={submitting} style={{ ...primaryButton, background: "var(--color-danger-text)" }}>
              {submitting ? "Salvando..." : "Confirmar não renovação"}
            </button>
            <button onClick={() => setCompleting(null)} style={smallButton}>Cancelar</button>
          </div>
        </div>
      )}
    </div>
  );
}

function NewRenewalForm({ clientId, onCreated, onError }: { clientId: string; onCreated: () => void; onError: (msg: string) => void }) {
  const [contractEndDate, setContractEndDate] = useState("");
  const [renewalValue, setRenewalValue] = useState("");
  const [riskNotes, setRiskNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!contractEndDate) {
      onError("Informe a data de vencimento do contrato.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post(`/clients/${clientId}/renewals`, {
        contract_end_date: contractEndDate,
        renewal_value: renewalValue ? Number(renewalValue) : null,
        risk_notes: riskNotes || null,
      });
      onCreated();
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Erro ao criar ciclo de renovação.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-control)", padding: "12px 14px", display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 10 }}>
      <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>
        Vencimento do contrato
        <input type="date" value={contractEndDate} onChange={(e) => setContractEndDate(e.target.value)} style={fieldInput} />
      </label>
      <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>
        Valor da renovação (R$)
        <input type="number" value={renewalValue} onChange={(e) => setRenewalValue(e.target.value)} style={fieldInput} />
      </label>
      <label style={{ fontSize: 12, color: "var(--text-secondary)", gridColumn: "1 / -1" }}>
        Notas de risco
        <textarea value={riskNotes} onChange={(e) => setRiskNotes(e.target.value)} style={{ ...fieldInput, minHeight: 50, resize: "vertical", fontFamily: "inherit" }} />
      </label>
      <div style={{ gridColumn: "1 / -1", display: "flex", justifyContent: "flex-end" }}>
        <button type="submit" disabled={submitting} style={primaryButton}>{submitting ? "Salvando..." : "Registrar ciclo de renovação"}</button>
      </div>
    </form>
  );
}

const fieldInput: CSSProperties = {
  display: "block",
  width: "100%",
  marginTop: 4,
  padding: "6px 8px",
  borderRadius: "var(--radius-control)",
  border: "0.5px solid var(--border-default)",
  fontSize: 13,
};

const smallButton: CSSProperties = {
  background: "transparent",
  border: "0.5px solid var(--border-default)",
  borderRadius: "var(--radius-control)",
  padding: "6px 10px",
  fontSize: 12,
  color: "var(--text-secondary)",
};

const primaryButton: CSSProperties = {
  background: "var(--color-blue)",
  color: "#fff",
  border: "none",
  borderRadius: "var(--radius-control)",
  padding: "7px 14px",
  fontSize: 13,
  fontWeight: 500,
};
