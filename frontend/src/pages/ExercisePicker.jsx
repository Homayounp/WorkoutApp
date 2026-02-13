import React, { useState } from 'react';
import API from '../api';

export default function ExercisePicker() {
  const [search, setSearch] = useState('');
  const [bodyPart, setBodyPart] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  

  const handleSearch = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (bodyPart) params.append('body_part', bodyPart);
      params.append('limit', '50');
      const res = await API.get(`/exercises/?${params.toString()}`);
      setResults(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>🔍 Exercise Library</h1>
      </div>

      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem' }}>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search exercises..."
          className="form-group"
          style={{ flex: 1, padding: '0.65rem', background: '#111', border: '1px solid #444', borderRadius: '6px', color: '#e0e0e0' }}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <select
          value={bodyPart}
          onChange={(e) => setBodyPart(e.target.value)}
          style={{ padding: '0.65rem', background: '#111', border: '1px solid #444', borderRadius: '6px', color: '#e0e0e0' }}
        >
          <option value="">All Body Parts</option>
          <option value="chest">Chest</option>
          <option value="back">Back</option>
          <option value="shoulders">Shoulders</option>
          <option value="upper arms">Upper Arms</option>
          <option value="lower arms">Lower Arms</option>
          <option value="upper legs">Upper Legs</option>
          <option value="lower legs">Lower Legs</option>
          <option value="waist">Waist</option>
          <option value="cardio">Cardio</option>
        </select>
        <button className="btn btn-primary" onClick={handleSearch} disabled={loading}>
          {loading ? '...' : 'Search'}
        </button>
      </div>
      

      {results.length > 0 && (
        <div className="table-container">
          <table>
            <thead>
              <tr><th>Name</th><th>Body Part</th><th>Target</th><th>Equipment</th></tr>
            </thead>
            <tbody>
              {results.map((ex) => (
                <tr key={ex.id}>
                  <td style={{ color: '#4fc3f7' }}>{ex.name}</td>
                  <td>{ex.body_part}</td>
                  <td>{ex.target}</td>
                  <td style={{ color: '#888' }}>{ex.equipment}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
