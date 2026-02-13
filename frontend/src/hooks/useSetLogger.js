import { useState, useCallback } from 'react';
import API from '../api';

/**
 * Handles all set logging: input state, logging, deletion.
 * Single responsibility: set-level CRUD operations.
 */
export default function useSetLogger(refreshActiveMeso) {
  const [logInputs, setLogInputs] = useState({});
  const [loggingSet, setLoggingSet] = useState(null);

  // ── Input management ──────────────────────────────
  const handleInputChange = useCallback((mdeId, setNum, field, value) => {
    const key = `${mdeId}-${setNum}`;
    setLogInputs((prev) => ({
      ...prev,
      [key]: {
        ...prev[key],
        [field]: value,
      },
    }));
  }, []);

  const getInputValue = useCallback((mdeId, setNum, field) => {
    const key = `${mdeId}-${setNum}`;
    return logInputs[key]?.[field] || '';
  }, [logInputs]);

  // ── Log a set ─────────────────────────────────────
  const handleLogSet = useCallback(async (mdeId, setNum, onSuccess) => {
    const key = `${mdeId}-${setNum}`;
    const inputs = logInputs[key];

    if (!inputs?.weight || !inputs?.reps) {
      alert('Please enter both weight and reps');
      return false;
    }

    setLoggingSet(key);

    try {
      await API.post(`/mesocycle-day-exercises/${mdeId}/log-set`, {
        set_number: setNum,
        weight: parseFloat(inputs.weight),
        reps: parseInt(inputs.reps),
      });

      // Clear input for this set
      setLogInputs((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });

      // Refresh mesocycle data and get updated state
      const updatedMeso = await refreshActiveMeso();

      // Notify caller (for muscle group completion check)
      if (onSuccess && updatedMeso) {
        onSuccess(updatedMeso);
      }

      return true;
    } catch (err) {
      console.error('Failed to log set:', err);
      alert('Failed to log set');
      return false;
    } finally {
      setLoggingSet(null);
    }
  }, [logInputs, refreshActiveMeso]);

  // ── Delete a set ──────────────────────────────────
  const handleDeleteSet = useCallback(async (setLogId) => {
    if (!window.confirm('Delete this set?')) return false;

    try {
      await API.delete(`/set-logs/${setLogId}`);
      await refreshActiveMeso();
      return true;
    } catch (err) {
      console.error('Failed to delete set:', err);
      alert('Failed to delete set');
      return false;
    }
  }, [refreshActiveMeso]);

  // ── Skip sets ─────────────────────────────────────
  const handleSkipSets = useCallback(async (mdeId, fromSet, toSet) => {
    try {
      await API.post(`/mesocycle-day-exercises/${mdeId}/skip-sets`, {
        from_set: fromSet,
        to_set: toSet,
      });
      await refreshActiveMeso();
      return true;
    } catch (err) {
      console.error('Failed to skip sets:', err);
      return false;
    }
  }, [refreshActiveMeso]);

  // ── Add extra set ─────────────────────────────────
  const handleAddSet = useCallback(async (mdeId) => {
    try {
      await API.post(`/mesocycle-day-exercises/${mdeId}/add-set`);
      await refreshActiveMeso();
      return true;
    } catch (err) {
      console.error('Failed to add set:', err);
      return false;
    }
  }, [refreshActiveMeso]);

  return {
    logInputs,
    loggingSet,
    handleInputChange,
    getInputValue,
    handleLogSet,
    handleDeleteSet,
    handleSkipSets,
    handleAddSet,
  };
}
