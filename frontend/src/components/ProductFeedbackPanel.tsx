import { useEffect, useState, type CSSProperties, type FormEvent } from "react";
import { api, ApiError } from "../api/client";
import StatusBadge from "./StatusBadge";
import {
  FEEDBACK_CATEGORY_LABELS,
  FEEDBACK_STATUS_LABELS,
  FEEDBACK_STATUS_TONE,
  type FeedbackCategory,
  type FeedbackStatus,
  type ProductFeedback,
} from "../types";

const CATEGORY_OPTIONS = Object.entries(FEEDBACK_CATEGORY_LABELS) as [FeedbackCategory, string][];
const STATUS_OPTIONS = Object.entries(FEEDBACK_STATUS_LABELS) as [FeedbackStatus, string][];

export default function ProductFeedbackPanel({ clientId }: { clientId: string }) {
  const [items, setItems] = useState<ProductFeedback[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  function load() {
    api.get<ProductFeedback[]>(`/clients/${clientId}/product-feedback`).then(setItems).catch(() => setItems([]));
  }

  useEffect(load, [clientId]);

  async function updateStatus(id: string, status: FeedbackStatus) {
    try {
      await api.patch(`/product-feedback/${id}`, { status });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao atualizar feedback.");
    }
  }

  return (
    <div style={{ background: "var(--surface-card)", border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-card)", padding: "16px 18px", display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <button onClick={() => setShowForm((v) => !v)} style={primaryButton}>
          {showForm ? "Cancelar" : "+ Novo feedback"}
        </button>
      </div>

      {error && <div style={{ fontSize: 13, color: "var(--color-danger-text)" }}>{error}</div>}

      {showForm && (
        <NewFeedbackForm clientId={clientId} onCreated={() => { setShowForm(false); load(); }} onError={setError} />
      )}

      {items?.length === 0 && <div style={{ fontSize: 12.5, color: "var(--text-muted)" }}>Nenhum feedback registrado ainda.</div>}
      {items?.map((fb) => (
        <div key={fb.id} style={{ border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-control)", padding: "10px 12px", display: "flex", flexDirection: "column", gap: 6 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ fontSize: 13, fontWeight: 500, color: "var(--color-graphite)" }}>{FEEDBACK_CATEGORY_LABELS[fb.category]}</div>
            <select value={fb.status} onChange={(e) => updateStatus(fb.id, e.target.value as FeedbackStatus)} style={fieldInput}>
              {STATUS_OPTIONS.map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>
          <div style={{ fontSize: 12.5, color: "var(--text-secondary)" }}>{fb.description}</div>
          <div><StatusBadge label={FEEDBACK_STATUS_LABELS[fb.status]} tone={FEEDBACK_STATUS_TONE[fb.status]} /></div>
        </div>
      ))}
    </div>
  );
}

function NewFeedbackForm({ clientId, onCreated, onError }: { clientId: string; onCreated: () => void; onError: (msg: string) => void }) {
  const [category, setCategory] = useState<FeedbackCategory>("melhoria");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!description) {
      onError("Descreva o feedback.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post(`/clients/${clientId}/product-feedback`, { category, description });
      onCreated();
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Erro ao registrar feedback.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-control)", padding: "12px 14px", display: "flex", flexDirection: "column", gap: 10 }}>
      <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>
        Categoria
        <select value={category} onChange={(e) => setCategory(e.target.value as FeedbackCategory)} style={fieldInput}>
          {CATEGORY_OPTIONS.map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
      </label>
      <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>
        Descrição
        <textarea value={description} onChange={(e) => setDescription(e.target.value)} style={{ ...fieldInput, minHeight: 50, resize: "vertical", fontFamily: "inherit" }} />
      </label>
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <button type="submit" disabled={submitting} style={primaryButton}>{submitting ? "Salvando..." : "Registrar feedback"}</button>
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
