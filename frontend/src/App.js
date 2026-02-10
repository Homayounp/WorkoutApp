import React, { useState, useEffect } from "react";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [users, setUsers] = useState([]);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  const [workouts, setWorkouts] = useState([]);
  const [wName, setWName] = useState("");
  const [wDesc, setWDesc] = useState("");
  const [wSets, setWSets] = useState(3);
  const [wReps, setWReps] = useState(10);
  const [wLoad, setWLoad] = useState(20);

  // -----------------------------
  // USERS
  // -----------------------------
  const fetchUsers = async () => {
    try {
      const res = await fetch(`${API_BASE}/users/`);
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
      const data = await res.json();
      setMessage(`User created: ${data.name}`);
      setName(""); setEmail(""); setPassword("");
      fetchUsers();
    } catch (err) {
      console.error(err);
      setMessage("Error creating user");
    }
  };

  // -----------------------------
  // WORKOUTS
  // -----------------------------
  const fetchWorkouts = async () => {
    try {
      const res = await fetch(`${API_BASE}/workouts/`);
      const data = await res.json();
      setWorkouts(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error(err);
      setWorkouts([]);
    }
  };

  const handleCreateWorkout = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/workouts/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: wName,
          description: wDesc,
          default_sets: wSets,
          default_reps: wReps,
          default_load: wLoad,
        }),
      });
      const data = await res.json();
      setMessage(`Workout created: ${data.name}`);
      setWName(""); setWDesc(""); setWSets(3); setWReps(10); setWLoad(20);
      fetchWorkouts();
    } catch (err) {
      console.error(err);
      setMessage("Error creating workout");
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchWorkouts();
  }, []);

  return (
    <div style={{ padding: "1.5rem", fontFamily: "sans-serif" }}>
      <h1>🏋️ Workout App (React)</h1>

      {/* --- Create User --- */}
      <form onSubmit={handleCreateUser} style={{ marginBottom: "1rem" }}>
        <input placeholder="Name" value={name} onChange={e => setName(e.target.value)} required />
        <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required />
        <input placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} required />
        <button type="submit">Create User</button>
      </form>

      {/* --- Create Workout --- */}
      <form onSubmit={handleCreateWorkout} style={{ marginBottom: "1rem" }}>
        <input placeholder="Workout name" value={wName} onChange={e => setWName(e.target.value)} required />
        <input placeholder="Description" value={wDesc} onChange={e => setWDesc(e.target.value)} required />
        <input type="number" placeholder="Sets" value={wSets} onChange={e => setWSets(Number(e.target.value))} />
        <input type="number" placeholder="Reps" value={wReps} onChange={e => setWReps(Number(e.target.value))} />
        <input type="number" placeholder="Load" value={wLoad} onChange={e => setWLoad(Number(e.target.value))} />
        <button type="submit">Create Workout</button>
      </form>

      <p>{message}</p>

      {/* --- Display Users --- */}
      <h2>Users</h2>
      <ul>
        {Array.isArray(users) && users.length > 0 ? users.map(u => <li key={u.id}>{u.name} — {u.email}</li>) : <li>No users found</li>}
      </ul>

      {/* --- Display Workouts --- */}
      <h2>Workouts</h2>
      <ul>
        {Array.isArray(workouts) && workouts.length > 0 ? workouts.map(w => (
          <li key={w.id}>{w.name} — {w.description} — {w.default_sets}x{w.default_reps} @ {w.default_load}kg</li>
        )) : <li>No workouts found</li>}
      </ul>
    </div>
  );
}

export default App;
