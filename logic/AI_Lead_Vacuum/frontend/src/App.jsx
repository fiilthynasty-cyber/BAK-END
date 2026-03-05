import React from "react";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import Leads from "./pages/Leads";

const NAV = [
  { label: "Dashboard", to: "/" },
  { label: "Leads", to: "/leads" },
];

const NavLink = ({ label, to }) => {
  const { pathname } = useLocation();
  const active = pathname === to;
  return (
    <Link
      to={to}
      style={{
        padding: "6px 14px",
        borderRadius: 6,
        textDecoration: "none",
        background: active ? "#2563eb" : "transparent",
        color: active ? "#fff" : "#374151",
        fontWeight: active ? 700 : 400,
        fontSize: "0.875rem",
      }}
    >
      {label}
    </Link>
  );
};

const Layout = () => (
  <>
    <header
      style={{
        background: "#fff",
        borderBottom: "1px solid #e5e7eb",
        padding: "12px 24px",
        display: "flex",
        alignItems: "center",
        gap: 16,
      }}
    >
      <strong style={{ fontSize: "1rem", marginRight: 16 }}>AI Lead Vacuum</strong>
      {NAV.map((n) => (
        <NavLink key={n.to} label={n.label} to={n.to} />
      ))}
    </header>
    <main style={{ maxWidth: 760, margin: "2rem auto", padding: "0 20px" }}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/leads" element={<Leads />} />
      </Routes>
    </main>
  </>
);

const App = () => (
  <BrowserRouter>
    <Layout />
  </BrowserRouter>
);

export default App;
