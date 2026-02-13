import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import API from '../api';

export default function Mesocycles() {
  const navigate = useNavigate();
  const [mesocycles, setMesocycles] = useState([]);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedPlanId, setSelectedPlanId] = useState('');
  const [mesoName, setMesoName] = useState('');
  const [creating, setCreating] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [mesoRes, planRes] = await Promise.all([
        API.get('/mesocycles/'),
        API.get('/plans/'),
      ]);
      setMesocycles(mesoRes.data);
      setPlans(planRes.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleCreate = async () => {
    if (!selectedPlanId || !mesoName.trim()) return;
    setCreating(true);
    try {
      const res = await API.post('/mesocycles/', {
        plan_id: parseInt(selectedPlanId),
        name: mesoName,
      });
      setShowCreate(false);
      setMesoName('');
      setSelectedPlanId('');
      fetchData();
      navigate(`/workout/${res.data.id}`);
    } catch (e) {
      alert('Failed: ' + (e.response?.data?.detail || e.message));
    } finally {
      setCreating(false);
    }
  };

  const advanceWeek = async (mesoId) => {
    try {
      await API.post(`/mesocycles/${mesoId}/next-week`);
      fetchData();
    } catch (e) {
      alert('Cannot advance: ' + (e.response?.data?.detail || e.message));
    }
  };

  const deleteMeso = async (mesoId) => {
    if (!window.confirm('Delete this mesocycle and all its data?')) return;
    try {
      await API.delete(`/mesocycles/${mesoId}`);
      fetchData();
    } catch (e) {
      alert('Failed: ' + (e.response?.data?.detail || e.message));
    }
  };

  if (loading) return <div className="loading">Loading...</div>;

  const activeMesos = mesocycles.filter((m) => m.is_active);
  const pastMesos = mesocycles.filter((m) => !m.is_active);

  return (
    <div>
      <div className="page-header">
        <h1>🔄 Mesocycles</h1>
        <button className="btn btn-primary" onClick={() => setShowCreate(!showCreate)}>
          {showCreate ? 'Cancel' : '+ Start New'}
        </button>
      </div>

      {showCreate && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div className="form-group">
            <label>Select Plan</label>
            <select value={selectedPlanId} onChange={(e) => setSelectedPlanId(e.target.value)}>
              <option value="">-- Choose a plan --</option>
              {plans.map((p) => (
                <option key={p.id} value={p.id}>{p.name} ({p.days?.length} days)</option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Mesocycle Name</label>
            <input
              value={mesoName}
              onChange={(e) => setMesoName(e.target.value)}
              placeholder="e.g. PPL Block 1"
            />
          </div>
          <button className="btn btn-success" onClick={handleCreate} disabled={creating}>
            {creating ? 'Starting...' : '🚀 Start Mesocycle'}
          </button>
        </div>
      )}

      {activeMesos.length > 0 && (
        <>
          <h2 style={{ fontSize: '1.1rem', color: '#4caf50', marginBottom: '0.75rem' }}>Active</h2>
          {activeMesos.map((m) => (
            <div key={m.id} className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">{m.name}</div>
                  <div className="card-subtitle">
                    Started {new Date(m.started_at).toLocaleDateString()}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span className="badge badge-active">Active</span>
                  <span className="badge badge-week">Week {m.current_week}</span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
                <button className="btn btn-primary btn-small" onClick={() => navigate(`/workout/${m.id}`)}>
                  💪 Workout
                </button>
                <button className="btn btn-secondary btn-small" onClick={() => advanceWeek(m.id)}>
                  ⏭ Next Week
                </button>
                <button className="btn btn-danger btn-small" onClick={() => deleteMeso(m.id)}>
                  Delete
                </button>
              </div>
            </div>
          ))}
        </>
      )}

      {pastMesos.length > 0 && (
        <>
          <h2 style={{ fontSize: '1.1rem', color: '#ff9800', marginTop: '1.5rem', marginBottom: '0.75rem' }}>History</h2>
          {pastMesos.map((m) => (
            <div key={m.id} className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">{m.name}</div>
                  <div className="card-subtitle">
                    {m.current_week} weeks · Started {new Date(m.started_at).toLocaleDateString()}
                  </div>
                </div>
                <div className="card-actions">
                  <span className="badge badge-inactive">Completed</span>
                  <button className="btn btn-danger btn-small" onClick={() => deleteMeso(m.id)}>
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </>
      )}

      {mesocycles.length === 0 && !showCreate && (
        <div className="card">
          <div className="card-subtitle">
            No mesocycles yet. Create a plan first, then start a mesocycle.
          </div>
        </div>
      )}
    </div>
  );
}
