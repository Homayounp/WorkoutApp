import React, { useState, useEffect } from "react";

function App() {
  const [users, setUsers] = useState([]);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  // Fetch all users (optional, once you have a /users/ GET route)
  const fetchUsers = async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/users/");
      if (!res.ok) throw new Error("Failed to fetch users");
      const data = await res.json();
      setUsers(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error(error);
      setUsers([]);
    }
  };

  // Create new user
  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch("http://127.0.0.1:8000/users/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error creating user");
      }

      const data = await res.json();
      setMessage(`User created: ${data.name}`);
      setName("");
      setEmail("");
      setPassword("");
      fetchUsers(); // refresh users list
    } catch (err) {
      console.error(err);
      setMessage("Error creating user.");
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>🏋️ Workout App</h1>

      <form onSubmit={handleCreateUser} style={{ marginBottom: "1rem" }}>
        <input
          placeholder="Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          style={{ marginRight: "10px" }}
        />
        <input
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          style={{ marginRight: "10px" }}
        />
        <input
          placeholder="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          style={{ marginRight: "10px" }}
        />
        <button type="submit">Create User</button>
      </form>

      <p>{message}</p>

      <h2>Users</h2>
      <ul>
        {users.length > 0 ? (
          users.map((user) => <li key={user.id}>{user.name} — {user.email}</li>)
        ) : (
          <li>No users found</li>
        )}
      </ul>
    </div>
  );
}

export default App;
