import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) return <div className="spinner" style={{ marginTop: "4rem" }}></div>;
  return user ? children : <Navigate to="/" replace />;
};

export default PrivateRoute;
