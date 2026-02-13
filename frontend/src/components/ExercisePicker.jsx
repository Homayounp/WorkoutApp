import React, { useState } from 'react';
import api from '../api';

export default function ExercisePicker({ onSelect, onClose }) {
  const [search, setSearch] = useState('');
  const [results, setResults] = useState([]);

  const doSearch = async (q) => {
    setSearch(q);
    if (q.length < 2) { setResults([]); return; }
    const res = await api.get('/exercises/', { params: { search: q, limit: 20 } });
    setResults(res.data);
  };

  return (
    <div style={overlay} onClick={onClose}>
      <div style={modal} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ color: '#e2e8f0', margin: 0 }}>Pick Exercise</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#ef4444', fontSize: 20, cursor: 'pointer' }}>✕</button>
        </div>
        <input placeholder="Search exercises..." value={search} onChange={e => doSearch(e.target.value)}
          style={inputStyle} autoFocus />
        <div style={{ maxHeight: 350, overflowY: 'auto' }}>
          {results.map(ex => (
            <div key={ex.id} onClick={() => onSelect(ex)} style={resultRow}>
              <span style={{ color: '#e2e8f0', fontSize: 14 }}>{ex.name}</span>
              <span style={{ color: '#64748b', fontSize: 11 }}>{ex.target} • {ex.body_part}</span>
            </div>
          ))}
          {search.length >= 2 && results.length === 0 && (
            <p style={{ color: '#64748b', textAlign: 'center', padding: 20 }}>No exercises found</p>
          )}
        </div>
      </div>
    </div>
  );
}

const overlay = { position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 };
const modal = { background: '#1e293b', borderRadius: 16, padding: 24, width: 450, maxHeight: '80vh', boxShadow: '0 8px 32px rgba(0,0,0,0.5)' };
const inputStyle = { width: '100%', padding: '10px 14px', marginBottom: 12, borderRadius: 8, border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0', fontSize: 14, outline: 'none', boxSizing: 'border-box' };
const resultRow = { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', cursor: 'pointer', borderRadius: 6, marginBottom: 2, background: '#0f172a', transition: 'background 0.15s' };
