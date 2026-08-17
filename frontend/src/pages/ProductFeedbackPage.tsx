import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import Pagination from "../components/Pagination";
import StatusBadge from "../components/StatusBadge";
import {
  FEEDBACK_CATEGORY_LABELS,
  FEEDBACK_STATUS_LABELS,
  FEEDBACK_STATUS_TONE,
  type Page,
  type ProductFeedbackWithClient,
} from "../types";

const PAGE_SIZE = 25;

export default function ProductFeedbackPage() {
  const [items, setItems] = useState<ProductFeedbackWithClient[] | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Page<ProductFeedbackWithClient>>(`/product-feedback?page=${page}&page_size=${PAGE_SIZE}`)
      .then((res) => {
        setItems(res.items);
        setTotal(res.total);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Erro ao carregar feedback."));
  }, [page]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <h1 style={{ fontSize: 20, color: "var(--color-graphite)" }}>Feedback de produto</h1>
      <div style={{ fontSize: 12.5, color: "var(--text-muted)" }}>
        Feedback registrado pelo CS em todas as contas, encaminhado para o time de Produto.
      </div>

      {error && <div style={{ fontSize: 13, color: "var(--color-danger-text)" }}>{error}</div>}

      <div style={{ background: "var(--surface-card)", border: "0.5px solid var(--border-default)", borderRadius: "var(--radius-card)", overflow: "hidden" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr 2.2fr 1fr", padding: "10px 16px", fontSize: 11.5, color: "var(--text-muted)", borderBottom: "0.5px solid var(--border-subtle)", letterSpacing: "0.03em" }}>
          <div>CLIENTE</div>
          <div>CATEGORIA</div>
          <div>DESCRIÇÃO</div>
          <div>STATUS</div>
        </div>
        {items === null && <div style={{ padding: 16, fontSize: 13, color: "var(--text-muted)" }}>Carregando...</div>}
        {items?.length === 0 && <div style={{ padding: 16, fontSize: 13, color: "var(--text-muted)" }}>Nenhum feedback registrado ainda.</div>}
        {items?.map((fb) => (
          <div key={fb.id} style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr 2.2fr 1fr", alignItems: "center", padding: "11px 16px", fontSize: 13, borderBottom: "0.5px solid var(--border-subtle)" }}>
            <Link to={`/clientes/${fb.client_id}`} style={{ color: "var(--color-blue)", fontWeight: 500 }}>
              {fb.client_name}
            </Link>
            <div style={{ color: "var(--text-secondary)" }}>{FEEDBACK_CATEGORY_LABELS[fb.category]}</div>
            <div style={{ color: "var(--text-secondary)" }}>{fb.description}</div>
            <div>
              <StatusBadge label={FEEDBACK_STATUS_LABELS[fb.status]} tone={FEEDBACK_STATUS_TONE[fb.status]} />
            </div>
          </div>
        ))}
        <Pagination page={page} pageSize={PAGE_SIZE} total={total} onPageChange={setPage} />
      </div>
    </div>
  );
}
