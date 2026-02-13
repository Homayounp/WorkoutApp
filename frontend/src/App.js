// frontend/src/App.js
import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  Link,
  useLocation,
} from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Plans from "./pages/Plans";
import Mesocycles from "./pages/Mesocycles";
import Workout from "./pages/Workout";
import Progress from "./pages/Progress";
import ExercisePicker from "./pages/ExercisePicker";

// ─── Private Route Guard ─────────────────────────────
function PrivateRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
          backgroundColor: "#0a0a0a",
        }}
      >
        <h1
          style={{
            fontSize: "2.8rem",
            fontWeight: "900",
            color: "#ffffff",
            letterSpacing: "0.3em",
            textTransform: "uppercase",
            marginBottom: "8px",
          }}
        >
          IRON PROTOCOL
        </h1>
        <p
          style={{
            fontSize: "0.9rem",
            color: "#666666",
            letterSpacing: "0.15em",
            textTransform: "uppercase",
            fontStyle: "italic",
            marginBottom: "32px",
          }}
        >
          Systematic destruction. Calculated growth.
        </p>
        <div className="loading-spinner" />
      </div>
    );
  }

  return user ? children : <Navigate to="/login" />;
}

// ─── Navigation Bar ──────────────────────────────────
function NavBar() {
  const { user, logout } = useAuth();
  const location = useLocation();

  if (!user) return null;

  const navItems = [
    { path: "/", label: "🏠 Home" },
    { path: "/plans", label: "📋 Plans" },
    { path: "/mesocycles", label: "🔄 Mesos" },
    { path: "/workout", label: "💪 Workout" },
    { path: "/progress", label: "📊 Progress" },
  ];

  return (
    <nav className="navbar">
      <div
        className="nav-brand"
        style={{
          display: "flex",
          flexDirection: "column",
          lineHeight: "1.1",
        }}
      >
        <span
          style={{
            fontWeight: "900",
            fontSize: "1.1rem",
            letterSpacing: "0.25em",
            color: "#ffffff",
            textTransform: "uppercase",
          }}
        >
          IRON PROTOCOL
        </span>
        <span
          style={{
            fontSize: "0.5rem",
            color: "#555555",
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            fontStyle: "italic",
          }}
        >
          Systematic destruction. Calculated growth.
        </span>
      </div>
      <div className="nav-links">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`nav-link ${
              location.pathname === item.path ? "active" : ""
            }`}
          >
            {item.label}
          </Link>
        ))}
      </div>
      <div className="nav-user">
        <span>{user.name}</span>
        <button onClick={logout} className="btn-logout">
          Logout
        </button>
      </div>
    </nav>
  );
}

// ─── App Root ────────────────────────────────────────
function App() {
  return (
    <AuthProvider>
      <Router>
        <NavBar />
        <div className="main-content">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <Dashboard />
                </PrivateRoute>
              }
            />
            <Route
              path="/plans"
              element={
                <PrivateRoute>
                  <Plans />
                </PrivateRoute>
              }
            />
            <Route
              path="/mesocycles"
              element={
                <PrivateRoute>
                  <Mesocycles />
                </PrivateRoute>
              }
            />
            <Route
              path="/workout"
              element={
                <PrivateRoute>
                  <Workout />
                </PrivateRoute>
              }
            />
            <Route
              path="/workout/:mesocycleId"
              element={
                <PrivateRoute>
                  <Workout />
                </PrivateRoute>
              }
            />
            <Route
              path="/progress"
              element={
                <PrivateRoute>
                  <Progress />
                </PrivateRoute>
              }
            />
            <Route
              path="/exercise-picker"
              element={
                <PrivateRoute>
                  <ExercisePicker />
                </PrivateRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
