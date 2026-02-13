import { useState, useEffect, useCallback } from 'react';
import API from '../api';

/**
 * Handles all mesocycle fetching, selection, and week/day navigation.
 * Single responsibility: data loading + navigation state.
 */
export default function useMesocycleLoader(mesocycleId) {
  const [mesocycles, setMesocycles] = useState([]);
  const [activeMeso, setActiveMeso] = useState(null);
  const [activeWeekIndex, setActiveWeekIndex] = useState(0);
  const [activeDayIndex, setActiveDayIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // ── Fetch single mesocycle detail ──────────────────
  const loadMesocycleDetail = useCallback(async (mesoId) => {
    try {
      const res = await API.get(`/mesocycles/${mesoId}`);
      setActiveMeso(res.data);

      const weekIdx = Math.max(0, (res.data.current_week || 1) - 1);
      setActiveWeekIndex(weekIdx);
      setActiveDayIndex(0);

      return res.data;
    } catch (err) {
      setError('Failed to load mesocycle details');
      console.error('loadMesocycleDetail error:', err);
      return null;
    }
  }, []);

  // ── Refresh active meso (after set log, etc.) ─────
  const refreshActiveMeso = useCallback(async () => {
    if (!activeMeso) return null;
    try {
      const res = await API.get(`/mesocycles/${activeMeso.id}`);
      setActiveMeso(res.data);
      return res.data;
    } catch (err) {
      console.error('refreshActiveMeso error:', err);
      return null;
    }
  }, [activeMeso?.id]);

  // ── Initial load ──────────────────────────────────
  useEffect(() => {
    const init = async () => {
      try {
        const res = await API.get('/mesocycles/');
        setMesocycles(res.data);

        if (mesocycleId) {
          const target = res.data.find((m) => m.id === parseInt(mesocycleId));
          if (target) {
            await loadMesocycleDetail(target.id);
          } else {
            setError('Mesocycle not found');
          }
        } else {
          const active = res.data.find((m) => m.is_active);
          if (active) {
            await loadMesocycleDetail(active.id);
          }
        }
      } catch (err) {
        setError('Failed to load mesocycles');
        console.error('init error:', err);
      } finally {
        setLoading(false);
      }
    };

    init();
  }, [mesocycleId, loadMesocycleDetail]);

  // ── Derived state ─────────────────────────────────
  const currentWeek = activeMeso?.weeks?.[activeWeekIndex] || null;
  const currentDay = currentWeek?.days?.[activeDayIndex] || null;

  return {
    // State
    mesocycles,
    activeMeso,
    activeWeekIndex,
    activeDayIndex,
    currentWeek,
    currentDay,
    loading,
    error,

    // Actions
    setActiveWeekIndex,
    setActiveDayIndex,
    loadMesocycleDetail,
    refreshActiveMeso,
  };
}
