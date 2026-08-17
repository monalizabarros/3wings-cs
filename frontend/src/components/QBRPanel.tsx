import { useEffect, useState, type CSSProperties, type FormEvent } from "react";
import { api, ApiError } from "../api/client";
import StatusBadge from "./StatusBadge";
import { QBR_STATUS_LABELS, QBR_STATUS_TONE, type QBR } from "../types";

export default function QBRPanel({ clientId }: { clientId: string }) {
  const [qbrs, setQbrs] = useState<QBR[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  function load() {
    api.get<QBR[]>(`/clients/${clientId}/qbrs`).then(setQbrs).catch(() => setQbrs([]));
  }

  useEffect(load, [clientId]);

  return (
    <div style={{ background: "var(--surface-card)", border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-card)", padding: "16px 18px", display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "flex-end" }}>
        <button onClick={() => setShowForm((v) => !v)} style={primaryButton}>
          {showForm ? "Cancelar" : "+ Agendar QBR"}
        </button>
      </div>

      {error && <div style={{ fontSize: 13, color: "var(--color-danger-text)" }}>{error}</div>}

      {showForm && (
        <NewQBRForm clientId={clientId} onCreated={() => { setShowForm(false); load(); }} onError={setError} />
      )}

      {qbrs?.length === 0 && <div style={{ fontSize: 12.5, color: "var(--text-muted)" }}>Nenhum QBR agendado ainda.</div>}
      {qbrs?.map((q) => (
        <QBRCard key={q.id} qbr={q} onChanged={load} onError={setError} />
      ))}
    </div>
  );
}

function QBRCard({ qbr, onChanged, onError }: { qbr: QBR; onChanged: () => void; onError: (msg: string) => void }) {
  const [completing, setCompleting] = useState(false);
  const [achievements, setAchievements] = useState("");
  const [challenges, setChallenges] = useState("");
  const [goals, setGoals] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [creatingPlan, setCreatingPlan] = useState(false);

  async function submitComplete(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post(`/qbrs/${qbr.id}/complete`, {
        achievements: achievements || null,
        challenges: challenges || null,
        next_period_goals: goals || null,
      });
      setCompleting(false);
      onChanged();
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Erro ao concluir QBR.");
    } finally {
      setSubmitting(false);
    }
  }

  async function createActionPlan() {
    setCreatingPlan(true);
    try {
      await api.post(`/qbrs/${qbr.id}/action-plan`);
      onChanged();
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Erro ao criar plano de ação.");
    } finally {
      setCreatingPlan(false);
    }
  }

  return (
    <div style={{ border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-control)", padding: "12px 14px", display: "flex", flexDirection: "column", gap: 8 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ fontSize: 13, fontWeight: 500, color: "var(--color-graphite)" }}>QBR — {qbr.scheduled_date}</div>
        <StatusBadge label={QBR_STATUS_LABELS[qbr.status]} tone={QBR_STATUS_TONE[qbr.status]} />
      </div>
      {qbr.agenda && <div style={{ fontSize: 12.5, color: "var(--text-secondary)" }}><strong>Pauta:</strong> {qbr.agenda}</div>}
      {qbr.participants && <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Participantes: {qbr.participants}</div>}

      {qbr.status === "realizado" && (
        <div style={{ fontSize: 12.5, color: "var(--text-secondary)", display: "flex", flexDirection: "column", gap: 4 }}>
          {qbr.achievements && <div><strong>Resultados:</strong> {qbr.achievements}</div>}
          {qbr.challenges && <div><strong>Desafios:</strong> {qbr.challenges}</div>}
          {qbr.next_period_goals && <div><strong>Metas do próximo período:</strong> {qbr.next_period_goals}</div>}
        </div>
      )}

      {qbr.status === "agendado" && !completing && (
        <button onClick={() => setCompleting(true)} style={{ ...smallButton, alignSelf: "flex-start" }}>
          Registrar realização
        </button>
      )}

      {completing && (
        <form onSubmit={submitComplete} style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <textarea placeholder="Resultados alcançados" value={achievements} onChange={(e) => setAchievements(e.target.value)} style={{ ...fieldInput, minHeight: 40 }} />
          <textarea placeholder="Desafios" value={challenges} onChange={(e) => setChallenges(e.target.value)} style={{ ...fieldInput, minHeight: 40 }} />
          <textarea placeholder="Metas do próximo período" value={goals} onChange={(e) => setGoals(e.target.value)} style={{ ...fieldInput, minHeight: 40 }} />
          <div style={{ display: "flex", gap: 8 }}>
            <button type="submit" disabled={submitting} style={primaryButton}>{submitting ? "Salvando..." : "Concluir QBR"}</button>
            <button type="button" onClick={() => setCompleting(false)} style={smallButton}>Cancelar</button>
          </div>
        </form>
      )}

      {qbr.status === "realizado" && (
        qbr.action_plan_id ? (
          <div style={{ fontSize: 11.5, color: "var(--color-blue)" }}>Plano de ação criado (ver em Planos de ação).</div>
        ) : (
          <button onClick={createActionPlan} disabled={creatingPlan} style={{ ...smallButton, alignSelf: "flex-start" }}>
            {creatingPlan ? "Criando..." : "Criar plano de ação"}
          </button>
        )
      )}
    </div>
  );
}

function NewQBRForm({ clientId, onCreated, onError }: { clientId: string; onCreated: () => void; onError: (msg: string) => void }) {
  const [scheduledDate, setScheduledDate] = useState("");
  const [participants, setParticipants] = useState("");
  const [agenda, setAgenda] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!scheduledDate) {
      onError("Informe a data do QBR.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post(`/clients/${clientId}/qbrs`, { scheduled_date: scheduledDate, participants: participants || null, agenda: agenda || null });
      onCreated();
    } catch (err) {
      onError(err instanceof ApiError ? err.message : "Erro ao agendar QBR.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-control)", padding: "12px 14px", display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 10 }}>
      <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>
        Data
        <input type="date" value={scheduledDate} onChange={(e) => setScheduledDate(e.target.value)} style={fieldInput} />
      </label>
      <label style={{ fontSize: 12, color: "var(--text-secondary)" }}>
        Participantes
        <input value={participants} onChange={(e) => setParticipants(e.target.value)} style={fieldInput} />
      </label>
      <label style={{ fontSize: 12, color: "var(--text-secondary)", gridColumn: "1 / -1" }}>
        Pauta
        <textarea value={agenda} onChange={(e) => setAgenda(e.target.value)} style={{ ...fieldInput, minHeight: 50, resize: "vertical", fontFamily: "inherit" }} />
      </label>
      <div style={{ gridColumn: "1 / -1", display: "flex", justifyContent: "flex-end" }}>
        <button type="submit" disabled={submitting} style={primaryButton}>{submitting ? "Salvando..." : "Agendar QBR"}</button>
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
