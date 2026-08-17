import { useEffect, useState, type CSSProperties, type FormEvent } from "react";
import { api, ApiError } from "../api/client";
import StatusBadge from "./StatusBadge";
import {
  EXPANSION_STAGE_LABELS,
  EXPANSION_STAGE_TONE,
  EXPANSION_TYPE_LABELS,
  type ExpansionOpportunity,
  type ExpansionStage,
  type ExpansionType,
} from "../types";

const TYPE_OPTIONS = Object.entries(EXPANSION_TYPE_LABELS) as [ExpansionType, string][];
const STAGE_OPTIONS = Object.entries(EXPANSION_STAGE_LABELS) as [ExpansionStage, string][];

export default function ExpansionPanel({ clientId }: { clientId: string }) {
  const [items, setItems] = useState<ExpansionOpportunity[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  function load() {
    api.get<ExpansionOpportunity[]>(`/clients/${clientId}/expansion-opportunities`).then(setItems).catch(() => setItems([]));
  }

  useEffect(load, [clientId]);

  async function updateStage(id: string, stage: ExpansionStage) {
    try {
      await api.patch(`/expansion-opportunities/${id}`, { stage });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao atualizar oportunidade.");
    }
  }

  return (
    <div style={{ background: "var(--surface-card)", border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-card)", padding: "16px 18px", display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <button onClick={() => setShowForm((v) => !v)} style={primaryButton}>
          {showForm ? "Cancelar" : "+ Nova oportunidade"}
        </button>
      </div>

      {error && <div style={{ fontSize: 13, color: "var(--color-danger-text)" }}>{error}</div>}

      {showForm && (
        <NewOpportunityForm clientId={clientId} onCreated={() => { setShowForm(false); load(); }} onError={setError} />
      )}

      {items?.length === 0 && <div style={{ fontSize: 12.5, color: "var(--text-muted)" }}>Nenhuma oportunidade de expansão registrada ainda.</div>}
      {items?.map((opp) => (
        <div key={opp.id} style={{ border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-control)", padding: "10px 12px", display: "flex", flexDirection: "column", gap: 6 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ fontSize: 13, fontWeight: 500, color: "var(--color-graphite)" }}>{EXPANSION_TYPE_LABELS[opp.type]}</div>
            <select value={opp.stage} onChange={(e) => updateStage(opp.id, e.target.value as ExpansionStage)} style={fieldInput}>
              {STAGE_OPTIONS.map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>
          <div style={{ fontSize: 12.5, color: "var(--text-secondary)" }}>{opp.description}</div>
          <div style={{ fontSize: 11.5, color: "var(--text-muted)" }}>
            {opp.estimated_value != null ? `Valor estimado: R$ ${opp.estimated_value.toLocaleString("pt-BR")}` : ""}
            {opp.probability != null ? ` · Probabilidade: ${opp.probability}%` : ""}
            {opp.expected_close_date ? ` · Previsão: ${opp.expected_close_date}` : ""}
          </div>
          <div><StatusBadge label={EXPANSION_STAGE_LABELS[opp.stage]} tone={EXPANSION_STAGE_TONE[opp.stage]} /></div>
        </div>
      ))}
    </div>
  );
}

function NewOpportunityForm({ clientId, onCreated, onError }: { clientId: string; onCreated: () => void; onError: (msg: string) => void }) {
  const [type, setType] = useState<ExpansionType>("upsell");
  const [description, setDescription] = useState("");
  const [estimatedValue, setEstimatedValue] = useState("");
  const [probability, setProbability] = useState("");
  const [expectedCloseDate, setExpectedCloseDate] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!description) {
      onError("Descreva a oportunidade.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post(`/clients/${clientId}/expansion-opportunities`, {
        type,
        description,
        estimated_value: estimatedValue ? Number(estimatedValue) : null,
        probability: probability ? Number(probability) : null,
        expected_close_date: expectedCloseDate || null,
      });
      onCreated();
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Erro ao criar oportunidade.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-control)", padding: "12px 14px", display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 10 }}>
      <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>
        Tipo
        <select value={type} onChange={(e) => setType(e.target.value as ExpansionType)} style={fieldInput}>
          {TYPE_OPTIONS.map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
      </label>
      <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>
        Previsão de fechamento
        <input type="date" value={expectedCloseDate} onChange={(e) => setExpectedCloseDate(e.target.value)} style={fieldInput} />
      </label>
      <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>
        Valor estimado (R$)
        <input type="number" value={estimatedValue} onChange={(e) => setEstimatedValue(e.target.value)} style={fieldInput} />
      </label>
      <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>
        Probabilidade (%)
        <input type="number" min={0} max={100} value={probability} onChange={(e) => setProbability(e.target.value)} style={fieldInput} />
      </label>
      <label style={{ fontSize: 12, color: "var(--text-secondary)", gridColumn: "1 / -1" }}>
        Descrição
        <textarea value={description} onChange={(e) => setDescription(e.target.value)} style={{ ...fieldInput, minHeight: 50, resize: "vertical", fontFamily: "inherit" }} />
      </label>
      <div style={{ gridColumn: "1 / -1", display: "flex", justifyContent: "flex-end" }}>
        <button type="submit" disabled={submitting} style={primaryButton}>{submitting ? "Salvando..." : "Registrar oportunidade"}</button>
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

const primaryButton: CSSProperties = {
  background: "var(--color-blue)",
  color: "#fff",
  border: "none",
  borderRadius: "var(--radius-control)",
  padding: "7px 14px",
  fontSize: 13,
  fontWeight: 500,
};
