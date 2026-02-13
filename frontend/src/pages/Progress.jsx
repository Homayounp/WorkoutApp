import React, { useState, useEffect } from 'react';
import API from '../api';

export default function Progress() {
  const [mesocycles, setMesocycles] = useState([]);
  const [selectedMeso, setSelectedMeso] = useState(null);
  const [mesoDetail, setMesoDetail] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    API.get('/mesocycles/')
      .then((res) => {
        setMesocycles(res.data);
        if (res.data.length > 0) {
          setSelectedMeso(res.data[0].id);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedMeso) return;
    API.get(`/mesocycles/${selectedMeso}`)
      .then((res) => setMesoDetail(res.data))
      .catch(console.error);
  }, [selectedMeso]);

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div>
      <div className="page-header">
        <h1>📊 Progress</h1>
      </div>

      <div className="form-group" style={{ marginBottom: '1.5rem' }}>
        <label>Select Mesocycle</label>
        <select value={selectedMeso || ''} onChange={(e) => setSelectedMeso(parseInt(e.target.value))}>
          {mesocycles.map((m) => (
            <option key={m.id} value={m.id}>
              {m.name} — Week {m.current_week} {m.is_active ? '(Active)' : '(Completed)'}
            </option>
          ))}
        </select>
      </div>

      {mesoDetail && mesoDetail.weeks?.map((week) => (
        <div key={week.id} className="card">
          <div className="card-title" style={{ marginBottom: '0.75rem' }}>
            Week {week.week_number}
          </div>
          {week.days?.map((day) => (
            <div key={day.id} style={{ marginBottom: '0.75rem', paddingLeft: '0.5rem', borderLeft: `3px solid ${day.is_completed ? '#4caf50' : '#444'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.35rem' }}>
                <strong style={{ fontSize: '0.9rem' }}>Day {day.day_order}</strong>
                <span className={`badge ${day.is_completed ? 'badge-active' : 'badge-inactive'}`}>
                  {day.is_completed ? 'Completed' : 'Pending'}
                </span>
              </div>
              {day.exercises?.map((mde) => (
                <div key={mde.id} style={{ fontSize: '0.8rem', color: '#ccc', marginBottom: '0.2rem', paddingLeft: '0.5rem' }}>
                  <span style={{ color: '#4fc3f7' }}>{mde.exercise.name}</span>
                  {mde.set_logs?.length > 0 && (
                    <span style={{ color: '#888', marginLeft: '0.5rem' }}>
                      — {mde.set_logs.map((s) => `${s.weight}kg×${s.reps}`).join(', ')}
                    </span>
                  )}
                </div>
              ))}
              {day.feedbacks?.length > 0 && (
                <div style={{ marginTop: '0.35rem', paddingLeft: '0.5rem' }}>
                  {day.feedbacks.map((fb) => (
                    <div key={fb.id} style={{ fontSize: '0.75rem', color: '#888' }}>
                      💬 {fb.muscle_group}: pump={fb.pump}, soreness={fb.soreness}, volume={fb.volume_feeling}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ))}

      {mesocycles.length === 0 && (
        <div className="card">
          <div className="card-subtitle">No mesocycles yet. Complete some workouts to see progress here.</div>
        </div>
      )}
    </div>
  );
}
