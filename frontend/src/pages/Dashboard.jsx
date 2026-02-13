import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import API from '../api';

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [activeMeso, setActiveMeso] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    API.get('/mesocycles/')
      .then((res) => {
        const active = res.data.find((m) => m.is_active);
        setActiveMeso(active || null);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div>
      <div className="page-header">
        <h1>Welcome, {user?.name} 👋</h1>
      </div>

      {activeMeso ? (
        <div className="card" onClick={() => navigate(`/workout/${activeMeso.id}`)} style={{ cursor: 'pointer' }}>
          <div className="card-header">
            <div>
              <div className="card-title">{activeMeso.name}</div>
              <div className="card-subtitle">Active Mesocycle</div>
            </div>
            <div>
              <span className="badge badge-active">Active</span>
              <span className="badge badge-week" style={{ marginLeft: '0.5rem' }}>
                Week {activeMeso.current_week}
              </span>
            </div>
          </div>
          <button className="btn btn-primary" style={{ marginTop: '0.75rem' }}>
            💪 Continue Workout
          </button>
        </div>
      ) : (
        <div className="card">
          <div className="card-title">No Active Mesocycle</div>
          <div className="card-subtitle" style={{ marginTop: '0.5rem' }}>
            Create a plan first, then start a mesocycle to begin tracking.
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}>
            <button className="btn btn-primary" onClick={() => navigate('/plans')}>
              📋 Create a Plan
            </button>
            <button className="btn btn-secondary" onClick={() => navigate('/mesocycles')}>
              🔄 Start Mesocycle
            </button>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
        <div className="card" onClick={() => navigate('/plans')} style={{ cursor: 'pointer' }}>
          <div className="card-title">📋 Plans</div>
          <div className="card-subtitle">Manage your workout templates</div>
        </div>
        <div className="card" onClick={() => navigate('/progress')} style={{ cursor: 'pointer' }}>
          <div className="card-title">📊 Progress</div>
          <div className="card-subtitle">View your training history</div>
        </div>
      </div>
    </div>
  );
}
