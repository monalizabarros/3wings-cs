import { useEffect, useState, type CSSProperties, type FormEvent } from "react";
import { api, ApiError } from "../api/client";
import StatusBadge from "./StatusBadge";
import {
  TICKET_SEVERITY_LABELS,
  TICKET_STATUS_LABELS,
  TICKET_STATUS_TONE,
  type SupportSummary,
  type SupportTicket,
  type TicketSeverity,
  type TicketStatus,
} from "../types";

const STATUS_OPTIONS = Object.entries(TICKET_STATUS_LABELS) as [TicketStatus, string][];

export default function SupportTicketsPanel({ clientId }: { clientId: string }) {
  const [tickets, setTickets] = useState<SupportTicket[] | null>(null);
  const [summary, setSummary] = useState<SupportSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  function load() {
    api.get<SupportTicket[]>(`/clients/${clientId}/support-tickets`).then(setTickets).catch(() => setTickets([]));
    api.get<SupportSummary>(`/clients/${clientId}/support-tickets/summary`).then(setSummary).catch(() => setSummary(null));
  }

  useEffect(load, [clientId]);

  async function updateTicket(id: string, patch: Partial<SupportTicket>) {
    try {
      await api.patch(`/support-tickets/${id}`, patch);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Erro ao atualizar ticket.");
    }
  }

  return (
    <div style={{ background: "var(--surface-card)", border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-card)", padding: "16px 18px", display: "flex", flexDirection: "column", gap: 12 }}>
      {summary && (
        <div style={{ display: "flex", gap: 16, fontSize: 12.5, color: "var(--text-muted)" }}>
          <div>Abertos: <strong style={{ color: "var(--text-secondary)" }}>{summary.open_tickets}</strong></div>
          <div>Críticos abertos: <strong style={{ color: "var(--text-secondary)" }}>{summary.critical_open_tickets}</strong></div>
          <div>Total: <strong style={{ color: "var(--text-secondary)" }}>{summary.total_tickets}</strong></div>
          <div>Satisfação média: <strong style={{ color: "var(--text-secondary)" }}>{summary.avg_satisfaction ?? "—"}</strong></div>
        </div>
      )}

      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <button onClick={() => setShowForm((v) => !v)} style={primaryButton}>
          {showForm ? "Cancelar" : "+ Novo ticket"}
        </button>
      </div>

      {error && <div style={{ fontSize: 13, color: "var(--color-danger-text)" }}>{error}</div>}

      {showForm && (
        <NewTicketForm clientId={clientId} onCreated={() => { setShowForm(false); load(); }} onError={setError} />
      )}

      {tickets?.length === 0 && <div style={{ fontSize: 12.5, color: "var(--text-muted)" }}>Nenhum ticket registrado ainda.</div>}
      {tickets?.map((t) => (
        <div key={t.id} style={{ border: t.severity === "critica" && t.status !== "resolvido" && t.status !== "fechado" ? "0.5px solid var(--color-danger-text)" : "0.5px solid var(--border-default)", borderRadius: "var(--radius-control)", padding: "10px 12px", display: "flex", flexDirection: "column", gap: 6 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div style={{ fontSize: 13, fontWeight: 500, color: "var(--color-graphite)" }}>{t.subject}</div>
            <select value={t.status} onChange={(e) => updateTicket(t.id, { status: e.target.value as TicketStatus })} style={fieldInput}>
              {STATUS_OPTIONS.map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>
          <div style={{ fontSize: 11.5, color: "var(--text-muted)" }}>
            Severidade: {TICKET_SEVERITY_LABELS[t.severity]} · Aberto em {t.opened_at}
            {t.closed_at ? ` · Fechado em ${t.closed_at}` : ""}
          </div>
          <div><StatusBadge label={TICKET_STATUS_LABELS[t.status]} tone={TICKET_STATUS_TONE[t.status]} /></div>
          {(t.status === "resolvido" || t.status === "fechado") && t.satisfaction_score === null && (
            <SatisfactionInput onSubmit={(score) => updateTicket(t.id, { satisfaction_score: score })} />
          )}
          {t.satisfaction_score !== null && (
            <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>Satisfação: {t.satisfaction_score}/5</div>
          )}
        </div>
      ))}
    </div>
  );
}

function SatisfactionInput({ onSubmit }: { onSubmit: (score: number) => void }) {
  const [score, setScore] = useState("");
  return (
    <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
      <select value={score} onChange={(e) => setScore(e.target.value)} style={fieldInput}>
        <option value="">Satisfação (1-5)</option>
        {[1, 2, 3, 4, 5].map((n) => (
          <option key={n} value={n}>{n}</option>
        ))}
      </select>
      <button
        type="button"
        disabled={!score}
        onClick={() => onSubmit(Number(score))}
        style={smallButton}
      >
        Registrar
      </button>
    </div>
  );
}

function NewTicketForm({ clientId, onCreated, onError }: { clientId: string; onCreated: () => void; onError: (msg: string) => void }) {
  const [subject, setSubject] = useState("");
  const [severity, setSeverity] = useState<TicketSeverity>("media");
  const [openedAt, setOpenedAt] = useState(new Date().toISOString().slice(0, 10));
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!subject) {
      onError("Informe o assunto do ticket.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post(`/clients/${clientId}/support-tickets`, { subject, severity, opened_at: openedAt });
      onCreated();
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Erro ao registrar ticket.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-control)", padding: "12px 14px", display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 10 }}>
      <label style={{ fontSize: 12, color: "var(--text-secondary)", gridColumn: "1 / -1" }}>
        Assunto
        <input value={subject} onChange={(e) => setSubject(e.target.value)} style={fieldInput} />
      </label>
      <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>
        Severidade
        <select value={severity} onChange={(e) => setSeverity(e.target.value as TicketSeverity)} style={fieldInput}>
          {Object.entries(TICKET_SEVERITY_LABELS).map(([value, label]) => (
            <option key={value} value={value}>{label}</option>
          ))}
        </select>
      </label>
      <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>
        Aberto em
        <input type="date" value={openedAt} onChange={(e) => setOpenedAt(e.target.value)} style={fieldInput} />
      </label>
      <div style={{ gridColumn: "1 / -1", display: "flex", justifyContent: "flex-end" }}>
        <button type="submit" disabled={submitting} style={primaryButton}>{submitting ? "Salvando..." : "Registrar ticket"}</button>
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
