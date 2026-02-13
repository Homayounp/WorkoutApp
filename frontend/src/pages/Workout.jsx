// frontend/src/pages/Workout.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import API from '../api';

// ─── Performance Verdict Icons ───────────────────────
const VerdictIcon = ({ verdict }) => {
  if (!verdict) return null;
  const icons = {
    improved: { emoji: '🔺', color: '#4caf50', label: 'Improved!' },
    hit: { emoji: '✅', color: '#4fc3f7', label: 'Target hit' },
    decreased: { emoji: '🔻', color: '#f44336', label: 'Below target' },
  };
  const v = icons[verdict] || icons.hit;
  return (
    <span
      title={v.label}
      style={{
        marginLeft: '8px',
        fontSize: '1.1rem',
        filter: verdict === 'improved' ? 'drop-shadow(0 0 4px #4caf50)' : 'none',
      }}
    >
      {v.emoji}
    </span>
  );
};

// ─── Progression Type Badge ──────────────────────────
const ProgressionBadge = ({ type, reason }) => {
  if (!type) return null;
  const badges = {
    add_set: { label: '+SET', color: '#4caf50', bg: 'rgba(76,175,80,0.15)' },
    add_reps: { label: '+REPS', color: '#4fc3f7', bg: 'rgba(79,195,247,0.15)' },
    add_weight: { label: '+WEIGHT', color: '#ff9800', bg: 'rgba(255,152,0,0.15)' },
    maintain: { label: 'MAINTAIN', color: '#888', bg: 'rgba(136,136,136,0.1)' },
    deload: { label: 'DELOAD', color: '#f44336', bg: 'rgba(244,67,54,0.15)' },
  };
  const b = badges[type] || badges.maintain;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
      <span
        style={{
          fontSize: '0.65rem',
          fontWeight: '800',
          color: b.color,
          backgroundColor: b.bg,
          padding: '2px 8px',
          borderRadius: '4px',
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
        }}
      >
        {b.label}
      </span>
      <span style={{ fontSize: '0.7rem', color: '#666', fontStyle: 'italic' }}>{reason}</span>
    </div>
  );
};

export default function Workout() {
  const { mesocycleId } = useParams();
  const navigate = useNavigate();

  const [mesocycles, setMesocycles] = useState([]);
  const [activeMesoId, setActiveMesoId] = useState(mesocycleId || null);
  const [day, setDay] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Set inputs: { [mde_id]: { [set_number]: { weight, reps } } }
  const [setInputs, setSetInputs] = useState({});
  const [loggedSets, setLoggedSets] = useState({});
  const [skippedExercises, setSkippedExercises] = useState({});
  const [notes, setNotes] = useState({});
  const [openMenu, setOpenMenu] = useState(null);

  // Smart progression targets: { [mde_id]: { type, reason, prescribed_sets, sets: { [set_number]: { weight, reps, is_new } } } }
  const [targets, setTargets] = useState({});

  // Verdicts after logging: { [mde_id]: { [set_number]: "hit" | "improved" | "decreased" } }
  const [verdicts, setVerdicts] = useState({});

  // History modal
  const [historyModal, setHistoryModal] = useState(null);
  const [historyData, setHistoryData] = useState([]);

  // Feedback modal
  const [feedbackModal, setFeedbackModal] = useState(null);
  const [feedbackValues, setFeedbackValues] = useState({});

  // Submitting states
  const [submittingSet, setSubmittingSet] = useState(null);
  const [completingDay, setCompletingDay] = useState(false);

  // Progression summary (after completing day)
  const [progression, setProgression] = useState(null);

  // ═══════════════════════════════════════════════════
  // DATA LOADING
  // ═══════════════════════════════════════════════════

  useEffect(() => {
    if (!mesocycleId) {
      API.get('/mesocycles/')
        .then((res) => {
          setMesocycles(res.data.filter((m) => m.is_active));
          const active = res.data.find((m) => m.is_active);
          if (active) setActiveMesoId(active.id);
        })
        .catch(console.error);
    }
  }, [mesocycleId]);

  // Fetch smart targets for the current day
  const fetchTargets = useCallback(async (dayId) => {
    try {
      const res = await API.get(`/mesocycle-days/${dayId}/smart-targets`);
      const targetsMap = {};
      (res.data.targets || []).forEach((t) => {
        const setsMap = {};
        (t.set_targets || []).forEach((st) => {
          setsMap[st.set_number] = {
            weight: st.target_weight,
            reps: st.target_reps,
            is_new: st.is_new_set,
          };
        });
        targetsMap[t.mde_id] = {
          type: t.progression_type,
          reason: t.reason,
          prescribed_sets: t.prescribed_sets,
          sets: setsMap,
        };
      });
      setTargets(targetsMap);
      return targetsMap;
    } catch (e) {
      console.log('No smart targets available (likely week 1)');
      return {};
    }
  }, []);

  // Fetch current workout day
  const fetchWorkout = useCallback(async () => {
    if (!activeMesoId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await API.get(`/mesocycles/${activeMesoId}/current-workout`);
      const dayData = res.data;
      setDay(dayData);

      // Fetch smart targets
      const targetsMap = await fetchTargets(dayData.id);

      // Initialize inputs from existing logs + smart targets
      const inputs = {};
      const logged = {};
      dayData.exercises?.forEach((mde) => {
        const mdeTarget = targetsMap[mde.id];
        const totalSets = mdeTarget?.prescribed_sets || mde.prescribed_sets;

        inputs[mde.id] = {};
        logged[mde.id] = {};

        for (let s = 1; s <= totalSets; s++) {
          const existingLog = mde.set_logs?.find((l) => l.set_number === s);
          if (existingLog) {
            inputs[mde.id][s] = {
              weight: existingLog.weight,
              reps: existingLog.reps,
            };
            logged[mde.id][s] = true;
          } else {
            inputs[mde.id][s] = { weight: '', reps: '' };
          }
        }
      });
      setSetInputs(inputs);
      setLoggedSets(logged);

      // Autofill ONLY for exercises with no targets and no logs (week 1 scenario)
      dayData.exercises?.forEach(async (mde) => {
        const hasTarget = targetsMap[mde.id]?.sets?.[1]?.weight > 0;
        if (!logged[mde.id]?.[1] && !hasTarget) {
          try {
            const autoRes = await API.get(`/exercises/${mde.exercise_id}/autofill`);
            if (autoRes.data?.weight) {
              setSetInputs((prev) => ({
                ...prev,
                [mde.id]: {
                  ...prev[mde.id],
                  1: { weight: autoRes.data.weight, reps: autoRes.data.reps },
                },
              }));
            }
          } catch (e) {
            /* no history */
          }
        }
      });
    } catch (e) {
      if (e.response?.status === 404) {
        setError('All workouts for this week are complete! Advance to the next week.');
        setDay(null);
      } else {
        setError('Failed to load workout');
      }
    } finally {
      setLoading(false);
    }
  }, [activeMesoId, fetchTargets]);

  useEffect(() => {
    fetchWorkout();
  }, [fetchWorkout]);

  // ═══════════════════════════════════════════════════
  // SET LOGGING + VERDICT
  // ═══════════════════════════════════════════════════

  const handleLogSet = async (mdeId, setNumber) => {
    const input = setInputs[mdeId]?.[setNumber];
    if (!input?.weight || !input?.reps) return;

    setSubmittingSet(`${mdeId}-${setNumber}`);
    try {
      const logRes = await API.post(`/mesocycle-day-exercises/${mdeId}/log-set`, {
        set_number: setNumber,
        weight: parseFloat(input.weight),
        reps: parseInt(input.reps),
      });

      setLoggedSets((prev) => ({
        ...prev,
        [mdeId]: { ...prev[mdeId], [setNumber]: true },
      }));

      // Evaluate performance vs target
      try {
        const evalRes = await API.post(`/sets/${logRes.data.id}/evaluate`);
        setVerdicts((prev) => ({
          ...prev,
          [mdeId]: {
            ...prev[mdeId],
            [setNumber]: evalRes.data.verdict,
          },
        }));
      } catch (e) {
        // No target to evaluate against — that's fine (week 1)
      }

      // Auto-fill next set with same weight if no target exists
      const nextSet = setNumber + 1;
      const mde = day?.exercises?.find((e) => e.id === mdeId);
      const totalSets = targets[mdeId]?.prescribed_sets || mde?.prescribed_sets || 0;
      if (nextSet <= totalSets && !loggedSets[mdeId]?.[nextSet]) {
        const nextTarget = targets[mdeId]?.sets?.[nextSet];
        if (!nextTarget || nextTarget.weight === 0) {
          setSetInputs((prev) => ({
            ...prev,
            [mdeId]: {
              ...prev[mdeId],
              [nextSet]: {
                weight: prev[mdeId]?.[nextSet]?.weight || input.weight,
                reps: prev[mdeId]?.[nextSet]?.reps || input.reps,
              },
            },
          }));
        }
      }

      // Check muscle group completion
      checkMuscleGroupComplete(mdeId);
    } catch (e) {
      alert('Failed to log set: ' + (e.response?.data?.detail || e.message));
    } finally {
      setSubmittingSet(null);
    }
  };

  const updateInput = (mdeId, setNumber, field, value) => {
    setSetInputs((prev) => ({
      ...prev,
      [mdeId]: {
        ...prev[mdeId],
        [setNumber]: {
          ...prev[mdeId]?.[setNumber],
          [field]: value,
        },
      },
    }));
  };

  // ═══════════════════════════════════════════════════
  // MUSCLE GROUP FEEDBACK CHECK
  // ═══════════════════════════════════════════════════

  const checkMuscleGroupComplete = (triggeredMdeId) => {
    if (!day) return;
    const triggeredExercise = day.exercises.find((e) => e.id === triggeredMdeId);
    if (!triggeredExercise) return;

    const muscleGroup = triggeredExercise.exercise.target;
    const sameGroupExercises = day.exercises.filter(
      (e) => e.exercise.target === muscleGroup
    );

    const allLogged = sameGroupExercises.every((mde) => {
      if (skippedExercises[mde.id]) return true;
      const totalSets = targets[mde.id]?.prescribed_sets || mde.prescribed_sets;
      for (let s = 1; s <= totalSets; s++) {
        if (!loggedSets[mde.id]?.[s]) return false;
      }
      return true;
    });

    const existingFeedback = day.feedbacks?.find((f) => f.muscle_group === muscleGroup);

    if (allLogged && !existingFeedback && !feedbackValues[muscleGroup]?.submitted) {
      setFeedbackModal(muscleGroup);
    }
  };

  // ═══════════════════════════════════════════════════
  // FEEDBACK SUBMISSION
  // ═══════════════════════════════════════════════════

  const submitFeedback = async () => {
    if (!feedbackModal || !day) return;
    const values = feedbackValues[feedbackModal] || {};
    try {
      await API.post(`/mesocycle-days/${day.id}/feedback`, {
        muscle_group: feedbackModal,
        soreness: values.soreness || 'none',
        pump: values.pump || 'none',
        volume_feeling: values.volume_feeling || 'just_right',
        notes: values.notes || '',
      });

      setFeedbackValues((prev) => ({
        ...prev,
        [feedbackModal]: { ...prev[feedbackModal], submitted: true },
      }));
      setFeedbackModal(null);

      // Re-fetch targets since feedback changes progression for remaining exercises
      if (day?.id) {
        await fetchTargets(day.id);
      }
    } catch (e) {
      alert('Failed to submit feedback: ' + (e.response?.data?.detail || e.message));
    }
  };

  // ═══════════════════════════════════════════════════
  // HISTORY
  // ═══════════════════════════════════════════════════

  const viewHistory = async (exerciseId, exerciseName) => {
    try {
      const res = await API.get(`/exercises/${exerciseId}/history`);
      setHistoryData(res.data);
      setHistoryModal(exerciseName);
    } catch (e) {
      setHistoryData([]);
      setHistoryModal(exerciseName);
    }
  };

  // ═══════════════════════════════════════════════════
  // SKIP / ADD SET
  // ═══════════════════════════════════════════════════

  const skipRemainingSets = (mdeId) => {
    setSkippedExercises((prev) => ({ ...prev, [mdeId]: true }));
    setOpenMenu(null);
    const mde = day?.exercises?.find((e) => e.id === mdeId);
    if (mde) {
      const totalSets = targets[mdeId]?.prescribed_sets || mde.prescribed_sets;
      const newLogged = { ...loggedSets };
      for (let s = 1; s <= totalSets; s++) {
        if (!newLogged[mdeId]?.[s]) {
          if (!newLogged[mdeId]) newLogged[mdeId] = {};
          newLogged[mdeId][s] = true;
        }
      }
      setLoggedSets(newLogged);
      setTimeout(() => checkMuscleGroupComplete(mdeId), 100);
    }
  };

  const addExtraSet = (mdeId) => {
    setOpenMenu(null);
    const mde = day?.exercises?.find((e) => e.id === mdeId);
    if (!mde) return;
    const totalSets = targets[mdeId]?.prescribed_sets || mde.prescribed_sets;
    const currentMax = Math.max(totalSets, ...Object.keys(setInputs[mdeId] || {}).map(Number));
    const newSetNum = currentMax + 1;

    setSetInputs((prev) => ({
      ...prev,
      [mdeId]: {
        ...prev[mdeId],
        [newSetNum]: { weight: '', reps: '' },
      },
    }));

    // Update local targets to include new set
    setTargets((prev) => ({
      ...prev,
      [mdeId]: {
        ...prev[mdeId],
        prescribed_sets: newSetNum,
        sets: {
          ...prev[mdeId]?.sets,
          [newSetNum]: { weight: 0, reps: 0, is_new: true },
        },
      },
    }));
  };

  // ═══════════════════════════════════════════════════
  // COMPLETE DAY
  // ═══════════════════════════════════════════════════

  const handleCompleteDay = async () => {
    if (!day) return;

    const muscleGroups = [...new Set(day.exercises.map((e) => e.exercise.target))];
    const existingFeedbackGroups = day.feedbacks?.map((f) => f.muscle_group) || [];
    const submittedGroups = Object.keys(feedbackValues).filter(
      (k) => feedbackValues[k]?.submitted
    );
    const allFeedbackGroups = [...new Set([...existingFeedbackGroups, ...submittedGroups])];
    const missingFeedback = muscleGroups.filter((g) => !allFeedbackGroups.includes(g));

    if (missingFeedback.length > 0) {
      setFeedbackModal(missingFeedback[0]);
      return;
    }

    setCompletingDay(true);
    try {
      await API.post(`/mesocycle-days/${day.id}/complete`);
      try {
        const progRes = await API.get(`/mesocycle-days/${day.id}/progression`);
        setProgression(progRes.data);
      } catch (e) {
        /* no progression */
      }
      fetchWorkout();
    } catch (e) {
      alert('Failed: ' + (e.response?.data?.detail || e.message));
    } finally {
      setCompletingDay(false);
    }
  };

  const isDayCompletable = () => {
    if (!day) return false;
    return day.exercises.every((mde) => {
      if (skippedExercises[mde.id]) return true;
      const totalSets = targets[mde.id]?.prescribed_sets || mde.prescribed_sets;
      for (let s = 1; s <= totalSets; s++) {
        if (!loggedSets[mde.id]?.[s]) return false;
      }
      return true;
    });
  };

  // ═══════════════════════════════════════════════════
  // RENDER
  // ═══════════════════════════════════════════════════

  if (loading) return <div className="loading">Loading workout...</div>;

  if (!activeMesoId) {
    return (
      <div>
        <div className="page-header">
          <h1>💪 Workout</h1>
        </div>
        <div className="card">
          <div className="card-subtitle">
            No active mesocycle. Start one from the Mesocycles page.
          </div>
          <button
            className="btn btn-primary"
            onClick={() => navigate('/mesocycles')}
            style={{ marginTop: '1rem' }}
          >
            Go to Mesocycles
          </button>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <div className="page-header">
          <h1>💪 Workout</h1>
        </div>
        <div className="card">
          <div className="card-subtitle">{error}</div>
          <button
            className="btn btn-secondary"
            onClick={() => navigate('/mesocycles')}
            style={{ marginTop: '1rem' }}
          >
            ⏭ Go to Mesocycles to advance week
          </button>
        </div>
        {progression && progression.length > 0 && (
          <div className="card" style={{ marginTop: '1rem' }}>
            <h3 style={{ color: '#4fc3f7', marginBottom: '0.75rem' }}>
              📊 Progression Summary
            </h3>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Exercise</th>
                    <th>Current Sets</th>
                    <th>Next Week</th>
                    <th>Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {progression.map((p, i) => (
                    <tr key={i}>
                      <td>{p.exercise_name}</td>
                      <td>{p.current_sets}</td>
                      <td
                        style={{
                          color:
                            p.recommended_sets > p.current_sets
                              ? '#4caf50'
                              : p.recommended_sets < p.current_sets
                              ? '#f44336'
                              : '#fff',
                          fontWeight: '700',
                        }}
                      >
                        {p.recommended_sets}
                      </td>
                      <td style={{ fontSize: '0.8rem', color: '#888' }}>{p.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    );
  }

  if (!day) return null;

  return (
    <div>
      <div className="page-header">
        <h1>💪 {day.plan_day?.name || 'Workout'}</h1>
        <span className="badge badge-week">Day {day.day_order}</span>
      </div>

      {day.exercises?.map((mde) => {
        const isSkipped = skippedExercises[mde.id];
        const mdeTarget = targets[mde.id];
        const totalSets = mdeTarget?.prescribed_sets || mde.prescribed_sets;

        return (
          <div
            key={mde.id}
            className="exercise-card"
            style={isSkipped ? { opacity: 0.5 } : {}}
          >
            {/* ── Exercise Header ─────────────────── */}
            <div className="exercise-header">
              <div>
                <span className="exercise-name">{mde.exercise.name}</span>
                <span className="exercise-target" style={{ marginLeft: '0.5rem' }}>
                  {mde.exercise.target}
                </span>
                <ProgressionBadge type={mdeTarget?.type} reason={mdeTarget?.reason} />
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <button
                  onClick={() => viewHistory(mde.exercise_id, mde.exercise.name)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#888',
                    cursor: 'pointer',
                    fontSize: '1.1rem',
                  }}
                  title="View history"
                >
                  🕐
                </button>

                <div className="menu-container">
                  <button
                    className="menu-trigger"
                    onClick={() => setOpenMenu(openMenu === mde.id ? null : mde.id)}
                  >
                    ⋮
                  </button>
                  {openMenu === mde.id && (
                    <div className="menu-dropdown">
                      <button
                        className="menu-item"
                        onClick={() => skipRemainingSets(mde.id)}
                      >
                        ⏭ Skip remaining sets
                      </button>
                      <button className="menu-item" onClick={() => addExtraSet(mde.id)}>
                        ➕ Add extra set
                      </button>
                      <button
                        className="menu-item"
                        onClick={() => {
                          const note = prompt('Add a note:', notes[mde.id] || '');
                          if (note !== null)
                            setNotes((prev) => ({ ...prev, [mde.id]: note }));
                          setOpenMenu(null);
                        }}
                      >
                        📝 Add note
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* ── Set Rows ────────────────────────── */}
            {Array.from({ length: totalSets }, (_, i) => i + 1).map((setNum) => {
              const isLogged = loggedSets[mde.id]?.[setNum];
              const input = setInputs[mde.id]?.[setNum] || { weight: '', reps: '' };
              const isSubmitting = submittingSet === `${mde.id}-${setNum}`;
              const setTarget = mdeTarget?.sets?.[setNum];
              const verdict = verdicts[mde.id]?.[setNum];
              const isNewSet = setTarget?.is_new;

              return (
                <div
                  key={setNum}
                  className={`set-row ${isLogged ? (isSkipped ? 'skipped' : 'logged') : ''}`}
                  style={
                    isNewSet && !isLogged
                      ? {
                          borderLeft: '3px solid #4caf50',
                          backgroundColor: 'rgba(76,175,80,0.05)',
                        }
                      : {}
                  }
                >
                  <span className="set-label" style={{ minWidth: '55px' }}>
                    {isNewSet ? '✨' : ''} Set {setNum}
                  </span>

                  {/* Weight input */}
                  <div style={{ position: 'relative' }}>
                    <input
                      type="number"
                      className="set-input"
                      placeholder={
                        setTarget?.weight > 0 ? String(setTarget.weight) : 'kg'
                      }
                      value={input.weight}
                      onChange={(e) => updateInput(mde.id, setNum, 'weight', e.target.value)}
                      disabled={isLogged || isSkipped}
                      style={{
                        color: isLogged ? '#aaa' : '#fff',
                      }}
                    />
                    {setTarget?.weight > 0 && !isLogged && !input.weight && (
                      <span
                        style={{
                          position: 'absolute',
                          right: '8px',
                          top: '50%',
                          transform: 'translateY(-50%)',
                          fontSize: '0.6rem',
                          color: '#555',
                          pointerEvents: 'none',
                        }}
                      >
                        target
                      </span>
                    )}
                  </div>
                  <span className="set-unit">kg</span>

                  {/* Reps input */}
                  <div style={{ position: 'relative' }}>
                    <input
                      type="number"
                      className="set-input"
                      placeholder={setTarget?.reps > 0 ? String(setTarget.reps) : 'reps'}
                      value={input.reps}
                      onChange={(e) => updateInput(mde.id, setNum, 'reps', e.target.value)}
                      disabled={isLogged || isSkipped}
                      style={{
                        color: isLogged ? '#aaa' : '#fff',
                      }}
                    />
                    {setTarget?.reps > 0 && !isLogged && !input.reps && (
                      <span
                        style={{
                          position: 'absolute',
                          right: '8px',
                          top: '50%',
                          transform: 'translateY(-50%)',
                          fontSize: '0.6rem',
                          color: '#555',
                          pointerEvents: 'none',
                        }}
                      >
                        target
                      </span>
                    )}
                  </div>
                  <span className="set-unit">reps</span>

                  {/* Log button + Verdict */}
                  <button
                    className="btn-log-set"
                    onClick={() => handleLogSet(mde.id, setNum)}
                    disabled={
                      isLogged || isSkipped || isSubmitting || !input.weight || !input.reps
                    }
                    style={
                      isLogged && verdict === 'improved'
                        ? { backgroundColor: 'rgba(76,175,80,0.3)' }
                        : {}
                    }
                  >
                    {isLogged ? '✓' : isSubmitting ? '...' : 'Log'}
                  </button>

                  {isLogged && <VerdictIcon verdict={verdict} />}
                </div>
              );
            })}

            {notes[mde.id] && (
              <div
                style={{
                  fontSize: '0.8rem',
                  color: '#888',
                  marginTop: '0.5rem',
                  fontStyle: 'italic',
                }}
              >
                📝 {notes[mde.id]}
              </div>
            )}
          </div>
        );
      })}

      {/* ── Complete Day Button ──────────────────── */}
      <button
        className="btn btn-success"
        style={{ width: '100%', marginTop: '1rem', padding: '0.85rem', fontSize: '1rem' }}
        onClick={handleCompleteDay}
        disabled={!isDayCompletable() || completingDay}
      >
        {completingDay ? 'Completing...' : '✅ Complete Workout Day'}
      </button>

      {/* ── History Modal ────────────────────────── */}
      {historyModal && (
        <div className="modal-overlay" onClick={() => setHistoryModal(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>🕐 {historyModal} — History</h3>
            {historyData.length === 0 ? (
              <p style={{ color: '#888' }}>No history found.</p>
            ) : (
              historyData.map((entry, i) => (
                <div key={i} className="history-entry">
                  <div className="history-date">
                    {new Date(entry.logged_at).toLocaleDateString()}
                  </div>
                  <div className="history-sets">
                    Set {entry.set_number}: {entry.weight}kg × {entry.reps} reps
                  </div>
                </div>
              ))
            )}
            <button
              className="btn btn-secondary"
              onClick={() => setHistoryModal(null)}
              style={{ marginTop: '1rem', width: '100%' }}
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* ── Feedback Modal ───────────────────────── */}
      {feedbackModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>💬 Feedback: {feedbackModal}</h3>
            <p style={{ color: '#888', fontSize: '0.85rem', marginBottom: '1rem' }}>
              How did <strong>{feedbackModal}</strong> feel today?
            </p>

            <div style={{ marginBottom: '1rem' }}>
              <label
                style={{
                  fontSize: '0.85rem',
                  color: '#aaa',
                  display: 'block',
                  marginBottom: '0.35rem',
                }}
              >
                Soreness (how sore is this muscle RIGHT NOW?)
              </label>
              <div className="feedback-option">
                {['none', 'light', 'moderate', 'severe'].map((v) => (
                  <button
                    key={v}
                    className={`feedback-btn ${
                      feedbackValues[feedbackModal]?.soreness === v ? 'selected' : ''
                    }`}
                    onClick={() =>
                      setFeedbackValues((prev) => ({
                        ...prev,
                        [feedbackModal]: { ...prev[feedbackModal], soreness: v },
                      }))
                    }
                  >
                    {v}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label
                style={{
                  fontSize: '0.85rem',
                  color: '#aaa',
                  display: 'block',
                  marginBottom: '0.35rem',
                }}
              >
                Pump (how was the pump during training?)
              </label>
              <div className="feedback-option">
                {['none', 'light', 'moderate', 'great'].map((v) => (
                  <button
                    key={v}
                    className={`feedback-btn ${
                      feedbackValues[feedbackModal]?.pump === v ? 'selected' : ''
                    }`}
                    onClick={() =>
                      setFeedbackValues((prev) => ({
                        ...prev,
                        [feedbackModal]: { ...prev[feedbackModal], pump: v },
                      }))
                    }
                  >
                    {v}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label
                style={{
                  fontSize: '0.85rem',
                  color: '#aaa',
                  display: 'block',
                  marginBottom: '0.35rem',
                }}
              >
                Volume Feeling (was the total volume...)
              </label>
              <div className="feedback-option">
                {['too_little', 'just_right', 'too_much'].map((v) => (
                  <button
                    key={v}
                    className={`feedback-btn ${
                      feedbackValues[feedbackModal]?.volume_feeling === v ? 'selected' : ''
                    }`}
                    onClick={() =>
                      setFeedbackValues((prev) => ({
                        ...prev,
                        [feedbackModal]: { ...prev[feedbackModal], volume_feeling: v },
                      }))
                    }
                  >
                    {v.replace(/_/g, ' ')}
                  </button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>Notes (optional)</label>
              <textarea
                rows={2}
                value={feedbackValues[feedbackModal]?.notes || ''}
                onChange={(e) =>
                  setFeedbackValues((prev) => ({
                    ...prev,
                    [feedbackModal]: { ...prev[feedbackModal], notes: e.target.value },
                  }))
                }
                placeholder="Anything worth noting..."
              />
            </div>

            <button
              className="btn btn-success"
              onClick={submitFeedback}
              style={{ width: '100%' }}
            >
              ✓ Submit Feedback
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
