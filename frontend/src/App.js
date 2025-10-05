// frontend/src/App.js
import React, { useState, useEffect } from "react";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [users, setUsers] = useState([]);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  const fetchUsers = async () => {
    try {
      const res = await fetch(`${API_BASE}/users/`);
      if (!res.ok) throw new Error("Failed to fetch users");
      const data = await res.json();
      setUsers(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("fetchUsers error:", error);
      setUsers([]);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/users/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(()=>({detail: "unknown"}));
        throw new Error(err.detail || "Error creating user");
      }
      const data = await res.json();
      setMessage(`User created: ${data.name}`);
      setName("");
      setEmail("");
      setPassword("");
      fetchUsers();
    } catch (err) {
      console.error("handleCreateUser error:", err);
      setMessage("Error creating user.");
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  return (
    <div style={{ padding: "1.5rem", fontFamily: "sans-serif" }}>
      <h1>🏋️ Workout App (React)</h1>

      <form onSubmit={handleCreateUser} style={{ marginBottom: "1rem" }}>
        <input placeholder="Name" value={name} onChange={(e)=>setName(e.target.value)} required style={{ marginRight: 8 }}/>
        <input placeholder="Email" value={email} onChange={(e)=>setEmail(e.target.value)} required style={{ marginRight: 8 }}/>
        <input placeholder="Password" type="password" value={password} onChange={(e)=>setPassword(e.target.value)} required style={{ marginRight: 8 }}/>
        <button type="submit">Create User</button>
      </form>

      <p>{message}</p>

      <h2>Users</h2>
      <ul>
        {Array.isArray(users) && users.length > 0 ? (
          users.map(u => <li key={u.id}>{u.name} — {u.email}</li>)
        ) : (
          <li>No users found</li>
        )}
      </ul>
    </div>
  );
}

export default App;
