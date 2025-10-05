import React, { useState, useEffect } from "react";

function App() {
  const [users, setUsers] = useState([]);
  const [newUser, setNewUser] = useState({ name: "", email: "", password: "" });

  // Fetch users from backend
  useEffect(() => {
    fetch("http://127.0.0.1:8000/users/")
      .then((res) => res.json())
      .then((data) => Array.isArray(data) ? setUsers(data) : setUsers([]))
      .catch(() => setUsers([]));
  }, []);

  // Create user
  const handleCreateUser = async (e) => {
    e.preventDefault();
    const response = await fetch("http://127.0.0.1:8000/users/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(newUser),
    });
    if (response.ok) {
      alert("User created!");
      setNewUser({ name: "", email: "", password: "" });
    } else {
      alert("Error creating user.");
    }
  };

  return (
    <div style={{ padding: "30px", fontFamily: "sans-serif" }}>
      <h1>🏋️ Workout App (Frontend)</h1>

      <h2>Create User</h2>
      <form onSubmit={handleCreateUser}>
        <input
          type="text"
          placeholder="Name"
          value={newUser.name}
          onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
          required
        />
        <input
          type="email"
          placeholder="Email"
          value={newUser.email}
          onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={newUser.password}
          onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
          required
        />
        <button type="submit">Add User</button>
      </form>

      <h2>All Users</h2>
      <ul>
        {users.length > 0 ? (
          users.map((u) => (
            <li key={u.id}>
              {u.name} ({u.email})
            </li>
          ))
        ) : (
          <li>No users yet.</li>
        )}
      </ul>
    </div>
  );
}

export default App;
