import { useState, useCallback, useRef } from 'react';

/**
 * Tracks muscle group completion and manages feedback popup queue.
 * Single responsibility: detect when muscle groups finish, queue popups.
 *
 * Core invariant: if feedback already exists for a muscle group on this day,
 * it must NEVER trigger again — even after refresh, navigation, or set deletion.
 */
export default function useMuscleGroupFeedback() {
  const [currentFeedbackMuscle, setCurrentFeedbackMuscle] = useState(null);
  const [feedbackQueue, setFeedbackQueue] = useState([]);
  const [completedFeedbacks, setCompletedFeedbacks] = useState(new Set());

  // Track muscle groups that were already complete when we loaded the page.
  // These should NOT trigger popups — only newly-completed groups should.
  const previouslyCompleteMuscles = useRef(new Set());
  const initialized = useRef(false);

  // ── Reset everything (on day/week change) ─────────
  const resetTracking = useCallback(() => {
    setCurrentFeedbackMuscle(null);
    setFeedbackQueue([]);
    setCompletedFeedbacks(new Set());
    previouslyCompleteMuscles.current = new Set();
    initialized.current = false;
  }, []);

  // ── Initialize from existing backend feedbacks ────
  const initializeFromExistingFeedbacks = useCallback((feedbacks) => {
    if (!feedbacks) return;
    const existing = new Set(feedbacks.map((fb) => fb.muscle_group));
    setCompletedFeedbacks(existing);
    existing.forEach((g) => previouslyCompleteMuscles.current.add(g));
  }, []);

  // ── Classify exercises by muscle group ────────────
  const groupByMuscle = useCallback((exercises) => {
    const groups = {};
    if (!exercises) return groups;

    exercises.forEach((mde) => {
      const group = mde.exercise?.body_part || 'Unknown';
      if (!groups[group]) groups[group] = [];
      groups[group].push(mde);
    });
    return groups;
  }, []);

  // ── Check if a specific muscle group is fully logged
  const isMuscleGroupComplete = useCallback((groupExercises) => {
    return groupExercises.every((mde) => {
      const logged = mde.set_logs?.length || 0;
      const prescribed = mde.prescribed_sets || 0;
      return prescribed > 0 && logged >= prescribed;
    });
  }, []);

  // ── Snapshot which muscles are already complete on load
  //    (so we don't trigger popups for them)
  const initializeCompletionSnapshot = useCallback((exercises) => {
    if (!exercises || initialized.current) return;
    initialized.current = true;

    const grouped = groupByMuscle(exercises);

    Object.entries(grouped).forEach(([group, exs]) => {
      if (isMuscleGroupComplete(exs)) {
        previouslyCompleteMuscles.current.add(group);
      }
    });
  }, [groupByMuscle, isMuscleGroupComplete]);

  // ── Check for newly completed muscle groups ───────
  //    Called AFTER every successful set log
  const checkForNewlyCompletedGroups = useCallback((exercises) => {
    if (!exercises) return;

    const grouped = groupByMuscle(exercises);

    Object.entries(grouped).forEach(([group, exs]) => {
      // Skip if we already handled this group
      if (completedFeedbacks.has(group)) return;
      if (previouslyCompleteMuscles.current.has(group)) return;

      if (isMuscleGroupComplete(exs)) {
        // Mark as previously complete so it won't trigger twice
        previouslyCompleteMuscles.current.add(group);

        // Show popup or queue it
        setCurrentFeedbackMuscle((current) => {
          if (!current) {
            return group;
          } else {
            // Already showing a popup — queue this one
            setFeedbackQueue((prev) =>
              prev.includes(group) ? prev : [...prev, group]
            );
            return current;
          }
        });
      }
    });
  }, [completedFeedbacks, groupByMuscle, isMuscleGroupComplete]);

  // ── Handle feedback submitted or skipped ──────────
  const handleFeedbackDone = useCallback((muscleGroup) => {
    setCompletedFeedbacks((prev) => new Set([...prev, muscleGroup]));
    setCurrentFeedbackMuscle(null);

    // Show next in queue after a brief pause for UX
    setTimeout(() => {
      setFeedbackQueue((prev) => {
        if (prev.length > 0) {
          const [next, ...rest] = prev;
          setCurrentFeedbackMuscle(next);
          return rest;
        }
        return prev;
      });
    }, 200);
  }, []);

  // ── Public API: check if a muscle group has feedback
  const hasFeedbackFor = useCallback((muscleGroup, dayFeedbacks) => {
    if (completedFeedbacks.has(muscleGroup)) return true;
    return dayFeedbacks?.some((f) => f.muscle_group === muscleGroup) || false;
  }, [completedFeedbacks]);

  return {
    // State
    currentFeedbackMuscle,
    feedbackQueue,
    completedFeedbacks,

    // Actions
    resetTracking,
    initializeFromExistingFeedbacks,
    initializeCompletionSnapshot,
    checkForNewlyCompletedGroups,
    handleFeedbackDone,

    // Utilities
    groupByMuscle,
    isMuscleGroupComplete,
    hasFeedbackFor,
  };
}
