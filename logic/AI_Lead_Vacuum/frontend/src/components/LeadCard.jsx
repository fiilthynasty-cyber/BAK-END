import React from "react";

const INTENT_COLOR = { high: "#ef4444", medium: "#f59e0b", low: "#94a3b8" };
const INTENT_LABEL = { high: "\uD83D\uDD25 HIGH", medium: "\u26A1 MED", low: "\u00B7 LOW" };

const LeadCard = ({ lead }) => {
  const { title, url, deep_link, source, score, intent, snippet, created_at_iso } = lead;
  const color = INTENT_COLOR[intent] ?? INTENT_COLOR.low;
  const label = INTENT_LABEL[intent] ?? (intent ?? "").toUpperCase();
  const href = deep_link || url || "#";
  const date = created_at_iso ? new Date(created_at_iso).toLocaleDateString() : null;

  return (
    <article
      style={{
        borderLeft: `4px solid ${color}`,
        borderRadius: 8,
        border: "1px solid #e5e7eb",
        borderLeftWidth: 4,
        padding: "12px 16px",
        marginBottom: 12,
        background: "#fff",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          style={{ fontWeight: 600, color: "#1a1a1a", textDecoration: "none", flex: 1 }}
        >
          {title || "Untitled"}
        </a>
        <span
          style={{
            marginLeft: 12,
            fontWeight: 700,
            fontSize: "0.75rem",
            background: color,
            color: "#fff",
            padding: "2px 8px",
            borderRadius: 999,
            whiteSpace: "nowrap",
          }}
        >
          {score}%
        </span>
      </div>
      <div style={{ marginTop: 6, fontSize: "0.75rem", color: "#555" }}>
        <span
          style={{
            background: "#eff6ff",
            color: "#2563eb",
            padding: "1px 7px",
            borderRadius: 999,
            marginRight: 6,
            fontWeight: 600,
          }}
        >
          {source}
        </span>
        <span style={{ color, fontWeight: 700, marginRight: 6 }}>{label}</span>
        {date && <span style={{ color: "#9ca3af" }}>{date}</span>}
      </div>
      {snippet && (
        <p
          style={{
            margin: "8px 0 0",
            fontSize: "0.8rem",
            color: "#444",
            lineHeight: 1.5,
            display: "-webkit-box",
            WebkitLineClamp: 3,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {snippet}
        </p>
      )}
    </article>
  );
};

export default LeadCard;
