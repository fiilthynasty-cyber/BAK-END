import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

// health
export const getHealth = () => client.get("/health").then((r) => r.data);

// leads CRUD
export const listLeads = (params) => client.get("/leads/", { params }).then((r) => r.data);
export const createLead = (payload) => client.post("/leads/", payload).then((r) => r.data);
export const deleteLead = (id) => client.delete(`/leads/${id}`).then((r) => r.data);

// pipeline
export const runPipeline = (payload) => client.post("/pipeline/run", payload).then((r) => r.data);

// analytics
export const getAnalyticsReport = (leads) =>
  client.post("/analytics/report", { leads }).then((r) => r.data);

// audit
export const auditSite = (url) => client.post("/audit/site", { url }).then((r) => r.data);

