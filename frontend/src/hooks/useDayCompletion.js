import { useCallback } from 'react';
import API from '../api';

/**
 * Handles day completion and progression advancement.
 * Single responsibility: day-level lifecycle operations.
 */
export default function useDayCompletion(refreshActiveMeso) {

  // ── Complete current day ──────────────────────────
  const handleCompleteDay = useCallback(async (dayId) => {
    try {
      await API.post(`/mesocycle-days/${dayId}/complete`);
      await refreshActiveMeso();
      return true;
    } catch (err) {
      console.error('Failed to complete day:', err);
      alert('Failed to complete day');
      return false;
    }
  }, [refreshActiveMeso]);

  // ── Advance to next week ──────────────────────────
  const handleAdvanceWeek = useCallback(async (mesocycleId) => {
    try {
      await API.post(`/mesocycles/${mesocycleId}/next-week`);
      await refreshActiveMeso();
      return true;
    } catch (err) {
      console.error('Failed to advance week:', err);
      const msg = err.response?.data?.detail || 'Failed to advance week';
      alert(msg);
      return false;
    }
  }, [refreshActiveMeso]);

  // ── Get progression preview ───────────────────────
  const getProgression = useCallback(async (dayId) => {
    try {
      const res = await API.get(`/mesocycle-days/${dayId}/progression`);
      return res.data;
    } catch (err) {
      console.error('Failed to get progression:', err);
      return [];
    }
  }, []);

  return {
    handleCompleteDay,
    handleAdvanceWeek,
    getProgression,
  };
}
