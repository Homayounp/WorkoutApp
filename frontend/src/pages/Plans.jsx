import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import API from '../api';

export default function Plans() {
  const navigate = useNavigate();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [planName, setPlanName] = useState('');
  const [days, setDays] = useState([{ name: '', order: 1, exercises: [] }]);
  const [creating, setCreating] = useState(false);

  // ── Exercise Picker Modal State ─────────────────────
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickerDayIndex, setPickerDayIndex] = useState(null);
  const [pickerBodyPart, setPickerBodyPart] = useState('');
  const [pickerTarget, setPickerTarget] = useState('');
  const [pickerSearch, setPickerSearch] = useState('');
  const [pickerResults, setPickerResults] = useState([]);
  const [pickerLoading, setPickerLoading] = useState(false);
  const [availableTargets, setAvailableTargets] = useState([]);

  const bodyParts = [
    'back', 'cardio', 'chest', 'lower arms', 'lower legs',
    'neck', 'shoulders', 'upper arms', 'upper legs', 'waist',
  ];

  const targetsByBodyPart = {
    'back': ['lats', 'upper back', 'spine', 'traps'],
    'chest': ['pectorals'],
    'shoulders': ['delts', 'serratus anterior'],
    'upper arms': ['biceps', 'triceps'],
    'lower arms': ['forearms'],
    'upper legs': ['glutes', 'hamstrings', 'quads', 'adductors', 'abductors'],
    'lower legs': ['calves'],
    'waist': ['abs', 'obliques'],
    'cardio': ['cardiovascular system'],
    'neck': ['levator scapulae'],
  };

  const fetchPlans = useCallback(() => {
    API.get('/plans/')
      .then((res) => setPlans(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchPlans(); }, [fetchPlans]);

  // ── Fetch exercises for picker ────────────────────
  const fetchPickerExercises = useCallback(async () => {
    setPickerLoading(true);
    try {
      const params = new URLSearchParams();
      if (pickerBodyPart) params.append('body_part', pickerBodyPart);
      if (pickerTarget) params.append('target', pickerTarget);
      if (pickerSearch) params.append('search', pickerSearch);
      params.append('limit', '100');
      const res = await API.get(`/exercises/?${params.toString()}`);
      setPickerResults(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setPickerLoading(false);
    }
  }, [pickerBodyPart, pickerTarget, pickerSearch]);

  // Re-fetch when filters change
  useEffect(() => {
    if (pickerOpen) {
      fetchPickerExercises();
    }
  }, [pickerOpen, fetchPickerExercises]);

  // Update available targets when body part changes
  useEffect(() => {
    if (pickerBodyPart) {
      setAvailableTargets(targetsByBodyPart[pickerBodyPart] || []);
      setPickerTarget(''); // reset target when body part changes
    } else {
      setAvailableTargets([]);
      setPickerTarget('');
    }
  }, [pickerBodyPart]);

  // ── Open picker for a specific day ────────────────
  const openPicker = (dayIndex) => {
    setPickerDayIndex(dayIndex);
    setPickerBodyPart('');
    setPickerTarget('');
    setPickerSearch('');
    setPickerResults([]);
    setPickerOpen(true);
  };

  // ── Add exercise from picker ──────────────────────
  const addExerciseFromPicker = (exercise) => {
    if (pickerDayIndex === null) return;
    const newDays = [...days];
    const exists = newDays[pickerDayIndex].exercises.find((e) => e.exercise_id === exercise.id);
    if (exists) return; // already added
    newDays[pickerDayIndex].exercises.push({
      exercise_id: exercise.id,
      order: newDays[pickerDayIndex].exercises.length + 1,
      name: exercise.name,
      target: exercise.target,
      body_part: exercise.body_part,
    });
    setDays(newDays);
  };

  const isExerciseAdded = (exerciseId) => {
    if (pickerDayIndex === null) return false;
    return days[pickerDayIndex].exercises.some((e) => e.exercise_id === exerciseId);
  };

  const removeExercise = (dayIndex, exIndex) => {
    const newDays = [...days];
    newDays[dayIndex].exercises.splice(exIndex, 1);
    newDays[dayIndex].exercises.forEach((e, i) => { e.order = i + 1; });
    setDays(newDays);
  };

  const addDay = () => {
    setDays([...days, { name: '', order: days.length + 1, exercises: [] }]);
  };

  const removeDay = (index) => {
    const newDays = days.filter((_, i) => i !== index);
    newDays.forEach((d, i) => { d.order = i + 1; });
    setDays(newDays);
  };

  const handleCreate = async () => {
    if (!planName.trim()) return;
    const hasEmptyDay = days.some((d) => !d.name.trim() || d.exercises.length === 0);
    if (hasEmptyDay) {
      alert('Each day must have a name and at least one exercise.');
      return;
    }
    setCreating(true);
    try {
      const payload = {
        name: planName,
        days: days.map((d) => ({
          name: d.name,
          order: d.order,
          exercises: d.exercises.map((e) => ({
            exercise_id: e.exercise_id,
            order: e.order,
          })),
        })),
      };
      await API.post('/plans/', payload);
      setPlanName('');
      setDays([{ name: '', order: 1, exercises: [] }]);
      setShowCreate(false);
      fetchPlans();
    } catch (e) {
      alert('Failed to create plan: ' + (e.response?.data?.detail || e.message));
    } finally {
      setCreating(false);
    }
  };

  const deletePlan = async (planId) => {
    if (!window.confirm('Delete this plan? This cannot be undone.')) return;
    try {
      await API.delete(`/plans/${planId}`);
      fetchPlans();
    } catch (e) {
      alert('Failed to delete: ' + (e.response?.data?.detail || e.message));
    }
  };

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div>
      <div className="page-header">
        <h1>📋 Training Plans</h1>
        <button className="btn btn-primary" onClick={() => setShowCreate(!showCreate)}>
          {showCreate ? 'Cancel' : '+ New Plan'}
        </button>
      </div>

      {/* ═══ CREATE FORM ═══ */}
      {showCreate && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div className="form-group">
            <label>Plan Name</label>
            <input
              value={planName}
              onChange={(e) => setPlanName(e.target.value)}
              placeholder="e.g. Push Pull Legs"
            />
          </div>

          {days.map((day, dayIndex) => (
            <div key={dayIndex} style={{
              background: '#111', borderRadius: '8px', padding: '1rem',
              marginBottom: '0.75rem', border: '1px solid #2a2a2a'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                <strong style={{ color: '#4fc3f7' }}>Day {day.order}</strong>
                {days.length > 1 && (
                  <button className="btn btn-danger btn-small" onClick={() => removeDay(dayIndex)}>Remove</button>
                )}
              </div>

              <div className="form-group">
                <input
                  value={day.name}
                  onChange={(e) => {
                    const newDays = [...days];
                    newDays[dayIndex].name = e.target.value;
                    setDays(newDays);
                  }}
                  placeholder="e.g. Push Day, Legs A"
                />
              </div>

              {/* Exercise list for this day */}
              {day.exercises.length > 0 && (
                <div style={{ marginBottom: '0.5rem' }}>
                  {day.exercises.map((ex, exIndex) => (
                    <div key={exIndex} style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      padding: '0.4rem 0.6rem', background: '#1a1a1a', borderRadius: '6px',
                      marginBottom: '0.3rem', border: '1px solid #333'
                    }}>
                      <div>
                        <span style={{ fontSize: '0.85rem', color: '#e0e0e0', fontWeight: 500 }}>
                          {ex.order}. {ex.name}
                        </span>
                        <span style={{
                          fontSize: '0.7rem', color: '#888', marginLeft: '0.5rem',
                          background: '#222', padding: '0.1rem 0.4rem', borderRadius: '4px'
                        }}>
                          {ex.target}
                        </span>
                      </div>
                      <button
                        onClick={() => removeExercise(dayIndex, exIndex)}
                        style={{
                          background: 'transparent', border: 'none', color: '#f44336',
                          cursor: 'pointer', fontSize: '1rem', padding: '0.2rem 0.4rem'
                        }}
                      >✕</button>
                    </div>
                  ))}
                </div>
              )}

              <button
                className="btn btn-secondary btn-small"
                onClick={() => openPicker(dayIndex)}
                style={{ marginTop: '0.25rem' }}
              >
                + Add Exercise
              </button>
            </div>
          ))}

          <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.75rem' }}>
            <button className="btn btn-secondary" onClick={addDay}>+ Add Day</button>
            <button className="btn btn-success" onClick={handleCreate} disabled={creating}>
              {creating ? 'Creating...' : '✓ Create Plan'}
            </button>
          </div>
        </div>
      )}

      {/* ═══ EXISTING PLANS LIST ═══ */}
      {plans.length === 0 && !showCreate ? (
        <div className="card">
          <div className="card-subtitle">No plans yet. Create your first training plan!</div>
        </div>
      ) : (
        plans.map((plan) => (
          <div key={plan.id} className="card">
            <div className="card-header">
              <div>
                <div className="card-title">{plan.name}</div>
                <div className="card-subtitle">
                  {plan.days?.length || 0} days · Created {new Date(plan.created_at).toLocaleDateString()}
                </div>
              </div>
              <div className="card-actions">
                <button className="btn btn-primary btn-small" onClick={() => navigate('/mesocycles')}>
                  Start Meso
                </button>
                <button className="btn btn-danger btn-small" onClick={() => deletePlan(plan.id)}>
                  Delete
                </button>
              </div>
            </div>
            {plan.days?.map((day) => (
              <div key={day.id} style={{ marginLeft: '0.5rem', marginBottom: '0.35rem' }}>
                <span style={{ color: '#4fc3f7', fontSize: '0.85rem', fontWeight: 600 }}>{day.name}:</span>
                <span style={{ color: '#888', fontSize: '0.8rem', marginLeft: '0.5rem' }}>
                  {day.exercises?.map((e) => e.exercise.name).join(', ')}
                </span>
              </div>
            ))}
          </div>
        ))
      )}

      {/* ═══════════════════════════════════════════════════
           EXERCISE PICKER MODAL
          ═══════════════════════════════════════════════════ */}
      {pickerOpen && (
        <div className="modal-overlay" onClick={() => setPickerOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{
            maxWidth: '650px', width: '95%', maxHeight: '85vh', display: 'flex', flexDirection: 'column'
          }}>
            {/* Modal Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0 }}>Choose Exercises</h3>
              <button
                onClick={() => setPickerOpen(false)}
                style={{
                  background: '#333', border: 'none', color: '#fff', width: '32px', height: '32px',
                  borderRadius: '50%', cursor: 'pointer', fontSize: '1rem'
                }}
              >✕</button>
            </div>

            {/* ── Filters ──────────────────────────────── */}
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
              {/* Body Part Filter */}
              <select
                value={pickerBodyPart}
                onChange={(e) => setPickerBodyPart(e.target.value)}
                style={{
                  flex: 1, minWidth: '140px', padding: '0.5rem', background: '#111',
                  border: '1px solid #444', borderRadius: '6px', color: '#e0e0e0', fontSize: '0.85rem'
                }}
              >
                <option value="">All Body Parts</option>
                {bodyParts.map((bp) => (
                  <option key={bp} value={bp}>{bp.charAt(0).toUpperCase() + bp.slice(1)}</option>
                ))}
              </select>

              {/* Target Muscle Filter */}
              <select
                value={pickerTarget}
                onChange={(e) => setPickerTarget(e.target.value)}
                disabled={!pickerBodyPart}
                style={{
                  flex: 1, minWidth: '140px', padding: '0.5rem', background: '#111',
                  border: `1px solid ${pickerBodyPart ? '#444' : '#2a2a2a'}`,
                  borderRadius: '6px', color: pickerBodyPart ? '#e0e0e0' : '#555', fontSize: '0.85rem'
                }}
              >
                <option value="">All Targets</option>
                {availableTargets.map((t) => (
                  <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                ))}
              </select>
            </div>

            {/* Search */}
            <input
              value={pickerSearch}
              onChange={(e) => setPickerSearch(e.target.value)}
              placeholder="🔍 Search by name..."
              style={{
                width: '100%', padding: '0.5rem 0.75rem', background: '#111',
                border: '1px solid #444', borderRadius: '6px', color: '#e0e0e0',
                fontSize: '0.85rem', marginBottom: '0.75rem'
              }}
            />

            {/* ── Body Part Quick Buttons ─────────────── */}
            {!pickerBodyPart && (
              <div style={{
                display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(110px, 1fr))',
                gap: '0.4rem', marginBottom: '0.75rem'
              }}>
                {bodyParts.map((bp) => (
                  <button
                    key={bp}
                    onClick={() => setPickerBodyPart(bp)}
                    style={{
                      padding: '0.6rem 0.5rem', background: '#1e1e1e', border: '1px solid #333',
                      borderRadius: '8px', color: '#4fc3f7', cursor: 'pointer', fontSize: '0.8rem',
                      fontWeight: 600, textTransform: 'capitalize', transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => { e.target.style.background = '#2a2a2a'; e.target.style.borderColor = '#4fc3f7'; }}
                    onMouseLeave={(e) => { e.target.style.background = '#1e1e1e'; e.target.style.borderColor = '#333'; }}
                  >
                    {bp}
                  </button>
                ))}
              </div>
            )}

            {/* ── Target Quick Buttons (when body part selected) ── */}
            {pickerBodyPart && !pickerTarget && availableTargets.length > 1 && (
              <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                {availableTargets.map((t) => (
                  <button
                    key={t}
                    onClick={() => setPickerTarget(t)}
                    style={{
                      padding: '0.4rem 0.75rem', background: '#1e1e1e', border: '1px solid #444',
                      borderRadius: '20px', color: '#ccc', cursor: 'pointer', fontSize: '0.8rem',
                      textTransform: 'capitalize', transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => { e.target.style.background = '#333'; }}
                    onMouseLeave={(e) => { e.target.style.background = '#1e1e1e'; }}
                  >
                    {t}
                  </button>
                ))}
              </div>
            )}

            {/* Active Filters Display */}
            {(pickerBodyPart || pickerTarget) && (
              <div style={{ display: 'flex', gap: '0.4rem', marginBottom: '0.75rem', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', color: '#888' }}>Filters:</span>
                {pickerBodyPart && (
                  <span style={{
                    background: '#2a2a4a', color: '#4fc3f7', padding: '0.2rem 0.6rem',
                    borderRadius: '12px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.3rem'
                  }}>
                    {pickerBodyPart}
                    <span
                      onClick={() => { setPickerBodyPart(''); setPickerTarget(''); }}
                      style={{ cursor: 'pointer', fontWeight: 'bold' }}
                    >✕</span>
                  </span>
                )}
                {pickerTarget && (
                  <span style={{
                    background: '#2a4a2a', color: '#4caf50', padding: '0.2rem 0.6rem',
                    borderRadius: '12px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.3rem'
                  }}>
                    {pickerTarget}
                    <span
                      onClick={() => setPickerTarget('')}
                      style={{ cursor: 'pointer', fontWeight: 'bold' }}
                    >✕</span>
                  </span>
                )}
                <button
                  onClick={() => { setPickerBodyPart(''); setPickerTarget(''); setPickerSearch(''); }}
                  style={{
                    background: 'transparent', border: 'none', color: '#888',
                    cursor: 'pointer', fontSize: '0.75rem', textDecoration: 'underline'
                  }}
                >Clear all</button>
              </div>
            )}

            {/* ── Exercise List ────────────────────────── */}
            <div style={{
              flex: 1, overflowY: 'auto', borderTop: '1px solid #333', paddingTop: '0.5rem'
            }}>
              {pickerLoading ? (
                <div style={{ textAlign: 'center', padding: '2rem', color: '#888' }}>Loading exercises...</div>
              ) : pickerResults.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '2rem', color: '#888' }}>
                  {pickerBodyPart || pickerSearch ? 'No exercises found. Try different filters.' : 'Select a body part to browse exercises.'}
                </div>
              ) : (
                <>
                  <div style={{ fontSize: '0.75rem', color: '#666', marginBottom: '0.5rem' }}>
                    {pickerResults.length} exercises found
                  </div>
                  {pickerResults.map((ex) => {
                    const added = isExerciseAdded(ex.id);
                    return (
                      <div
                        key={ex.id}
                        onClick={() => !added && addExerciseFromPicker(ex)}
                        style={{
                          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                          padding: '0.6rem 0.75rem', marginBottom: '0.3rem', background: added ? '#1a2e1a' : '#1a1a1a',
                          border: `1px solid ${added ? '#2d5a2d' : '#2a2a2a'}`, borderRadius: '8px',
                          cursor: added ? 'default' : 'pointer', transition: 'all 0.15s'
                        }}
                        onMouseEnter={(e) => { if (!added) { e.currentTarget.style.background = '#252525'; e.currentTarget.style.borderColor = '#4fc3f7'; } }}
                        onMouseLeave={(e) => { if (!added) { e.currentTarget.style.background = '#1a1a1a'; e.currentTarget.style.borderColor = '#2a2a2a'; } }}
                      >
                        <div>
                          <div style={{ fontSize: '0.9rem', color: added ? '#4caf50' : '#e0e0e0', fontWeight: 500 }}>
                            {added && '✓ '}{ex.name}
                          </div>
                          <div style={{ fontSize: '0.72rem', color: '#777', marginTop: '0.15rem' }}>
                            {ex.body_part} → {ex.target} · {ex.equipment || 'bodyweight'}
                          </div>
                        </div>
                        {!added && (
                          <span style={{
                            background: '#4fc3f7', color: '#000', padding: '0.25rem 0.6rem',
                            borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600, flexShrink: 0
                          }}>
                            + Add
                          </span>
                        )}
                      </div>
                    );
                  })}
                </>
              )}
            </div>

            {/* Modal Footer */}
            <div style={{ borderTop: '1px solid #333', paddingTop: '0.75rem', marginTop: '0.5rem' }}>
              <button
                className="btn btn-primary"
                onClick={() => setPickerOpen(false)}
                style={{ width: '100%' }}
              >
                Done ({pickerDayIndex !== null ? days[pickerDayIndex]?.exercises.length : 0} exercises selected)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
