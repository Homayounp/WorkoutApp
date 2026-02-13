import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api';

export default function MesocycleDetail() {
  const { mesocycleId } = useParams();
  const navigate = useNavigate();
  const [meso, setMeso] = useState(null);
  const [expandedWeek, setExpandedWeek] = useState(null);

  useEffect(() => {
    api.get(`/mesocycles/${mesocycleId}`).then(r => {
      setMeso(r.data);
      // Auto-expand current week
      if (r.data.weeks?.length > 0) {
        setExpandedWeek(r.data.current_week);
      }
    }).catch(() => navigate('/mesocycles'));
  }, [mesocycleId, navigate]);

  if (!meso) return <div style={{ padding: 40, color: '#94a3b8', textAlign: 'center' }}>Loading...</div>;

  return (
    <div style={{ padding: 32, maxWidth: 900, margin: '0 auto' }}>
      <button onClick={() => navigate('/mesocycles')} style={btnBack}>← Back to Mesocycles</button>

      <h1 style={{ color: '#f1f5f9', marginBottom: 4 }}>{meso.name}</h1>
      <p style={{ color: '#94a3b8', marginBottom: 24 }}>
        Week {meso.current_week} •{' '}
        <span style={{ color: meso.is_active ? '#22c55e' : '#ef4444' }}>
          {meso.is_active ? 'Active' : 'Completed'}
        </span>
      </p>

      {meso.weeks?.sort((a, b) => a.week_number - b.week_number).map(week => (
        <div key={week.id} style={{ marginBottom: 16 }}>
          <div
            onClick={() => setExpandedWeek(expandedWeek === week.week_number ? null : week.week_number)}
            style={{
              background: week.week_number === meso.current_week ? '#1e3a5f' : '#1e293b',
              borderRadius: 10, padding: '14px 20px', cursor: 'pointer',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              border: week.week_number === meso.current_week ? '1px solid #3b82f6' : '1px solid transparent',
            }}
          >
            <h3 style={{ color: '#e2e8f0', fontSize: 16, margin: 0 }}>
              Week {week.week_number}
              {week.week_number === meso.current_week && (
                <span style={{ background: '#3b82f6', color: '#fff', fontSize: 10, padding: '2px 8px', borderRadius: 10, marginLeft: 10 }}>CURRENT</span>
              )}
            </h3>
            <span style={{ color: '#64748b' }}>{expandedWeek === week.week_number ? '▼' : '▶'}</span>
          </div>

          {expandedWeek === week.week_number && (
            <div style={{ marginTop: 8 }}>
              {week.days?.sort((a, b) => a.day_order - b.day_order).map(day => (
                <div key={day.id} style={{
                  background: '#0f172a', borderRadius: 8, padding: 16, marginBottom: 8,
                  borderLeft: `3px solid ${day.is_completed ? '#22c55e' : '#64748b'}`,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <h4 style={{ color: '#e2e8f0', margin: 0 }}>
                      {day.day_name || `Day ${day.day_order}`}
                      <span style={{
                        marginLeft: 10, fontSize: 11, padding: '2px 8px', borderRadius: 8,
                        background: day.is_completed ? '#166534' : '#44403c',
                        color: day.is_completed ? '#86efac' : '#a8a29e',
                      }}>
                        {day.is_completed ? '✓ Complete' : 'Pending'}
                      </span>
                    </h4>
                  </div>

                  {day.exercises?.map(ex => (
                    <div key={ex.id} style={{ marginLeft: 12, marginBottom: 8 }}>
                      <p style={{ color: '#94a3b8', fontSize: 13, fontWeight: 600, marginBottom: 4 }}>
                        {ex.exercise?.name}
                        <span style={{ color: '#64748b', fontWeight: 400 }}> — {ex.prescribed_sets} sets</span>
                        {ex.note && <span style={{ color: '#f59e0b', fontWeight: 400, fontSize: 11, marginLeft: 8 }}>📝 {ex.note}</span>}
                      </p>
                      {ex.set_logs?.length > 0 && (
                        <div style={{ marginLeft: 12 }}>
                          {ex.set_logs.sort((a, b) => a.set_number - b.set_number).map(sl => (
                            <span key={sl.id} style={{
                              display: 'inline-block', background: sl.weight === 0 ? '#44403c' : '#1e3a5f',
                              color: sl.weight === 0 ? '#a8a29e' : '#93c5fd', fontSize: 11,
                              padding: '2px 8px', borderRadius: 4, marginRight: 4, marginBottom: 2,
                            }}>
                              {sl.weight === 0 ? `S${sl.set_number}: Skipped` : `S${sl.set_number}: ${sl.weight}kg × ${sl.reps}`}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}

                  {day.feedbacks?.length > 0 && (
                    <div style={{ marginTop: 8, padding: '8px 12px', background: '#1e293b', borderRadius: 6 }}>
                      <p style={{ color: '#64748b', fontSize: 11, marginBottom: 4 }}>Feedback:</p>
                      {day.feedbacks.map(fb => (
                        <p key={fb.id} style={{ color: '#94a3b8', fontSize: 11, margin: 0 }}>
                          <strong>{fb.muscle_group}:</strong> soreness={fb.soreness}, pump={fb.pump}, volume={fb.volume_feeling}
                        </p>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

const btnBack = {
  background: 'none', border: '1px solid #334155', color: '#94a3b8',
  padding: '8px 16px', borderRadius: 8, cursor: 'pointer', marginBottom: 20,
  fontSize: 13, display: 'block',
};
