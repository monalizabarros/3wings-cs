import type { CSSProperties } from "react";

export default function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
}: {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  if (total === 0) return null;

  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, total);

  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 16px", fontSize: 12.5, color: "var(--text-muted)" }}>
      <div>
        {start}–{end} de {total}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <button onClick={() => onPageChange(page - 1)} disabled={page <= 1} style={buttonStyle(page <= 1)}>
          Anterior
        </button>
        <div>
          Página {page} de {totalPages}
        </div>
        <button onClick={() => onPageChange(page + 1)} disabled={page >= totalPages} style={buttonStyle(page >= totalPages)}>
          Próxima
        </button>
      </div>
    </div>
  );
}

function buttonStyle(disabled: boolean): CSSProperties {
  return {
    background: "transparent",
    border: "0.5px solid var(--border-default)",
    borderRadius: "var(--radius-control)",
    padding: "5px 10px",
    fontSize: 12,
    color: disabled ? "var(--text-muted)" : "var(--text-secondary)",
    opacity: disabled ? 0.5 : 1,
    cursor: disabled ? "default" : "pointer",
  };
}
