import React from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const Navbar = () => {
  const { user, logout } = useAuth();
  const loc = useLocation();

  if (!user) return null;

  const links = [
    { to: "/dashboard", label: "Dashboard" },
    { to: "/plans", label: "Plans" },
    { to: "/mesocycles", label: "Mesocycles" },
  ];

  return (
    <nav
      style={{
        background: "#1a1a1a",
        borderBottom: "1px solid #2a2a2a",
        padding: "0.75rem 0",
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}
    >
      <div
        className="container flex items-center justify-between"
      >
        <Link to="/dashboard" style={{ fontWeight: 700, fontSize: "1.2rem" }}>
          <span style={{ color: "#6366f1" }}>Hyper</span>Track
        </Link>

        <div className="flex items-center gap-1">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              style={{
                padding: "0.4rem 0.8rem",
                borderRadius: 8,
                fontSize: "0.9rem",
                background: loc.pathname === l.to ? "#2a2a2a" : "transparent",
                color: loc.pathname === l.to ? "#6366f1" : "#888",
              }}
            >
              {l.label}
            </Link>
          ))}
          <button
            onClick={logout}
            style={{
              padding: "0.4rem 0.8rem",
              borderRadius: 8,
              background: "transparent",
              color: "#666",
              fontSize: "0.85rem",
              marginLeft: "0.5rem",
            }}
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
