import React from "react";
import { getHealth, listLeads } from "../services/api";

const Stat = ({ label, value, color = "#1a1a1a" }) => (
  <div
    style={{
      flex: "1 1 120px",
      background: "#fff",
      border: "1px solid #e5e7eb",
      borderRadius: 10,
      padding: "16px 20px",
      textAlign: "center",
    }}
  >
    <div style={{ fontSize: "1.8rem", fontWeight: 700, color }}>{value}</div>
    <div style={{ fontSize: "0.75rem", color: "#666", marginTop: 4 }}>{label}</div>
  </div>
);

const Dashboard = () => {
  const [leads, setLeads] = React.useState([]);
  const [apiStatus, setApiStatus] = React.useState("checking...");

  React.useEffect(() => {
    getHealth()
      .then((d) => setApiStatus(d.status ?? "ok"))
      .catch(() => setApiStatus("unreachable"));
    listLeads()
      .then((data) => setLeads(Array.isArray(data) ? data : []))
      .catch(() => {});
  }, []);

  const hot = leads.filter((l) => l.score >= 80).length;
  const highIntent = leads.filter((l) => l.intent === "high").length;

  return (
    <section>
      <h2 style={{ margin: "0 0 16px" }}>Dashboard</h2>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 24 }}>
        <Stat label="Total Leads" value={leads.length || "\u2014"} />
        <Stat label="Hot Leads (\u226580)" value={hot || "\u2014"} color="#ef4444" />
        <Stat label="High Intent" value={highIntent || "\u2014"} color="#2563eb" />
      </div>
      <p style={{ fontSize: "0.75rem", color: apiStatus === "ok" ? "#16a34a" : "#dc2626", marginBottom: 20 }}>
        API: {apiStatus}
      </p>
      {leads.length > 0 && (
        <div>
          <h3 style={{ margin: "0 0 12px", fontSize: "0.9rem", color: "#374151" }}>Recent Leads</h3>
          {leads.slice(0, 5).map((l) => (
            <div
              key={l.id}
              style={{ margin: "8px 0", border: "1px solid #e5e7eb", borderRadius: 8, padding: "12px 16px" }}
            >
              <strong>{l.business_name || l.url}</strong>
              {" "}
              <span
                style={{
                  background: l.score >= 80 ? "#fef2f2" : "#f3f4f6",
                  color: l.score >= 80 ? "#dc2626" : "#374151",
                  borderRadius: 4,
                  padding: "1px 6px",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                }}
              >
                {l.score}
              </span>
              <span style={{ marginLeft: 8, fontSize: "0.75rem", color: "#6b7280" }}>{l.intent}</span>
              {l.ai_reason && (
                <p style={{ margin: "4px 0 0", fontSize: "0.8rem", color: "#6b7280" }}>{l.ai_reason}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
};

export default Dashboard;
