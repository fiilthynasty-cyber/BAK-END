import React from "react";
import LeadCard from "../components/LeadCard";
import { runPipeline, listLeads } from "../services/api";

const defaultForm = {
  url: "",
  name: "",
  niche: "",
  keywords: "",
  locations: "",
};

const Leads = () => {
  const [form, setForm] = React.useState(defaultForm);
  const [leads, setLeads] = React.useState([]);
  const [dbLeads, setDbLeads] = React.useState([]);
  const [summary, setSummary] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState(null);

  const refreshDbLeads = () =>
    listLeads().then((data) => setDbLeads(Array.isArray(data) ? data : [])).catch(() => {});

  React.useEffect(() => { refreshDbLeads(); }, []);

  const handleChange = (e) =>
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  const handleRun = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const payload = {
        user_id: "frontend-user",
        company: {
          url: form.url || "https://example.com",
          name: form.name || undefined,
          niche: form.niche || undefined,
          keywords: form.keywords.split(",").map((k) => k.trim()).filter(Boolean),
          locations: form.locations.split(",").map((l) => l.trim()).filter(Boolean),
        },
        min_score: 30,
        sources: ["reddit", "hn"],
      };
      const result = await runPipeline(payload);
      setLeads(result.leads || []);
      setSummary(result.summary || null);
      refreshDbLeads();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = {
    width: "100%",
    padding: "8px 10px",
    border: "1px solid #d1d5db",
    borderRadius: 6,
    fontSize: "0.875rem",
    marginBottom: 10,
    boxSizing: "border-box",
  };

  return (
    <section>
      <h2 style={{ margin: "0 0 16px" }}>Find Leads</h2>

      <form onSubmit={handleRun} style={{ marginBottom: 24 }}>
        <input
          style={inputStyle} name="url" placeholder="Company URL (required)"
          value={form.url} onChange={handleChange}
        />
        <input
          style={inputStyle} name="name" placeholder="Company name"
          value={form.name} onChange={handleChange}
        />
        <input
          style={inputStyle} name="niche" placeholder="Niche / industry (e.g. project management)"
          value={form.niche} onChange={handleChange}
        />
        <input
          style={inputStyle} name="keywords" placeholder="Keywords, comma-separated"
          value={form.keywords} onChange={handleChange}
        />
        <input
          style={inputStyle} name="locations" placeholder="Locations, comma-separated (optional)"
          value={form.locations} onChange={handleChange}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            background: "#2563eb", color: "#fff", border: "none",
            padding: "10px 22px", borderRadius: 7, cursor: "pointer",
            fontWeight: 600, fontSize: "0.875rem",
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? "Scanning..." : "Run Pipeline"}
        </button>
      </form>

      {error && (
        <p style={{ color: "#dc2626", marginBottom: 16, fontSize: "0.875rem" }}>
          Error: {error}
        </p>
      )}

      {summary && (
        <div style={{ marginBottom: 20, fontSize: "0.8rem", color: "#555" }}>
          {summary.total_leads} leads &middot; {summary.hot_leads} hot &middot; {summary.queries_run} queries run
        </div>
      )}

      {leads.map((lead, i) => (
        <LeadCard key={lead.url + i} lead={lead} />
      ))}

      {!loading && leads.length === 0 && !error && (
        <p style={{ color: "#9ca3af", fontSize: "0.875rem" }}>Enter details above and run the pipeline to find leads.</p>
      )}

      {dbLeads.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h3 style={{ margin: "0 0 12px", fontSize: "0.9rem", color: "#374151", borderTop: "1px solid #e5e7eb", paddingTop: 20 }}>
            All Saved Leads ({dbLeads.length})
          </h3>
          {dbLeads.map((l) => (
            <div key={l.id} style={{ margin: "8px 0", border: "1px solid #e5e7eb", borderRadius: 8, padding: "12px 16px" }}>
              <strong>{l.business_name || l.url}</strong>
              {" "}
              <span style={{ background: "#f3f4f6", borderRadius: 4, padding: "1px 6px", fontSize: "0.75rem", fontWeight: 600 }}>{l.score}</span>
              <span style={{ marginLeft: 8, fontSize: "0.75rem", color: "#6b7280" }}>{l.intent}</span>
              {l.source && <span style={{ marginLeft: 8, fontSize: "0.7rem", color: "#9ca3af" }}>{l.source}</span>}
            </div>
          ))}
        </div>
      )}
    </section>
  );
};

export default Leads;
