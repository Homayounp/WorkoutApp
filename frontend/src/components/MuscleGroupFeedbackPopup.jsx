import React, { useState } from 'react';
import API from '../api';

const MuscleGroupFeedbackPopup = ({ muscleGroup, mesoDayId, onClose, onSubmitted }) => {
  const [soreness, setSoreness] = useState('none');
  const [pump, setPump] = useState('none');
  const [volumeFeeling, setVolumeFeeling] = useState('just_right');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await API.post(`/mesocycle-days/${mesoDayId}/feedback`, {
        muscle_group: muscleGroup,
        soreness,
        pump,
        volume_feeling: volumeFeeling,
        notes: notes || null,
      });
      onSubmitted(muscleGroup);
    } catch (err) {
      console.error('Failed to submit feedback:', err);
      alert('Failed to submit feedback. Try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const sorenessOptions = [
    { value: 'none', label: 'None', emoji: '😊', color: '#4ade80' },
    { value: 'light', label: 'Light', emoji: '😐', color: '#facc15' },
    { value: 'moderate', label: 'Moderate', emoji: '😣', color: '#fb923c' },
    { value: 'severe', label: 'Severe', emoji: '😵', color: '#ef4444' },
  ];

  const pumpOptions = [
    { value: 'none', label: 'No Pump', emoji: '💨', color: '#94a3b8' },
    { value: 'light', label: 'Light', emoji: '💪', color: '#60a5fa' },
    { value: 'moderate', label: 'Moderate', emoji: '🔥', color: '#a78bfa' },
    { value: 'great', label: 'Great', emoji: '🚀', color: '#4ade80' },
  ];

  const volumeOptions = [
    { value: 'too_little', label: 'Too Little', emoji: '📉', color: '#60a5fa' },
    { value: 'just_right', label: 'Just Right', emoji: '✅', color: '#4ade80' },
    { value: 'too_much', label: 'Too Much', emoji: '📈', color: '#ef4444' },
  ];

  return (
    <div style={styles.overlay}>
      <div style={styles.popup}>
        <div style={styles.header}>
          <div style={styles.headerIcon}>💬</div>
          <h2 style={styles.title}>
            How did <span style={styles.muscleHighlight}>{muscleGroup}</span> feel?
          </h2>
          <p style={styles.subtitle}>
            You've completed all {muscleGroup.toLowerCase()} exercises. Rate your session.
          </p>
        </div>

        <div style={styles.section}>
          <label style={styles.sectionLabel}>Soreness (from previous session)</label>
          <div style={styles.optionRow}>
            {sorenessOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setSoreness(opt.value)}
                style={{
                  ...styles.optionButton,
                  backgroundColor: soreness === opt.value ? opt.color + '22' : '#1a1a1a',
                  borderColor: soreness === opt.value ? opt.color : '#333',
                  color: soreness === opt.value ? opt.color : '#888',
                }}
              >
                <span style={styles.optionEmoji}>{opt.emoji}</span>
                <span style={styles.optionLabel}>{opt.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div style={styles.section}>
          <label style={styles.sectionLabel}>Pump Quality</label>
          <div style={styles.optionRow}>
            {pumpOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setPump(opt.value)}
                style={{
                  ...styles.optionButton,
                  backgroundColor: pump === opt.value ? opt.color + '22' : '#1a1a1a',
                  borderColor: pump === opt.value ? opt.color : '#333',
                  color: pump === opt.value ? opt.color : '#888',
                }}
              >
                <span style={styles.optionEmoji}>{opt.emoji}</span>
                <span style={styles.optionLabel}>{opt.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div style={styles.section}>
          <label style={styles.sectionLabel}>Volume Feeling</label>
          <div style={styles.optionRow}>
            {volumeOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setVolumeFeeling(opt.value)}
                style={{
                  ...styles.optionButton,
                  backgroundColor: volumeFeeling === opt.value ? opt.color + '22' : '#1a1a1a',
                  borderColor: volumeFeeling === opt.value ? opt.color : '#333',
                  color: volumeFeeling === opt.value ? opt.color : '#888',
                }}
              >
                <span style={styles.optionEmoji}>{opt.emoji}</span>
                <span style={styles.optionLabel}>{opt.label}</span>
              </button>
            ))}
          </div>
        </div>

        <div style={styles.section}>
          <label style={styles.sectionLabel}>Notes (optional)</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder={`Any notes about your ${muscleGroup.toLowerCase()} session...`}
            style={styles.textarea}
            rows={2}
          />
        </div>

        <div style={styles.actions}>
          <button onClick={onClose} style={styles.skipButton} disabled={submitting}>
            Skip
          </button>
          <button onClick={handleSubmit} style={styles.submitButton} disabled={submitting}>
            {submitting ? 'Saving...' : 'Submit Feedback'}
          </button>
        </div>
      </div>
    </div>
  );
};

const styles = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.88)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 9999,
    backdropFilter: 'blur(4px)',
  },
  popup: {
    backgroundColor: '#111111',
    border: '1px solid #2a2a2a',
    borderRadius: '16px',
    padding: '28px',
    width: '90%',
    maxWidth: '460px',
    maxHeight: '90vh',
    overflowY: 'auto',
  },
  header: {
    textAlign: 'center',
    marginBottom: '24px',
  },
  headerIcon: {
    fontSize: '2.2rem',
    marginBottom: '8px',
  },
  title: {
    fontSize: '1.25rem',
    fontWeight: '700',
    color: '#ffffff',
    margin: '0 0 6px 0',
  },
  muscleHighlight: {
    color: '#a78bfa',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  subtitle: {
    fontSize: '0.78rem',
    color: '#666',
    margin: 0,
  },
  section: {
    marginBottom: '18px',
  },
  sectionLabel: {
    display: 'block',
    fontSize: '0.75rem',
    fontWeight: '600',
    color: '#aaa',
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    marginBottom: '8px',
  },
  optionRow: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap',
  },
  optionButton: {
    flex: '1',
    minWidth: '75px',
    padding: '10px 6px',
    border: '1.5px solid #333',
    borderRadius: '10px',
    cursor: 'pointer',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '4px',
    transition: 'all 0.2s ease',
    backgroundColor: '#1a1a1a',
  },
  optionEmoji: {
    fontSize: '1.2rem',
  },
  optionLabel: {
    fontSize: '0.65rem',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
  },
  textarea: {
    width: '100%',
    padding: '10px 12px',
    backgroundColor: '#1a1a1a',
    border: '1px solid #333',
    borderRadius: '8px',
    color: '#e0e0e0',
    fontSize: '0.85rem',
    resize: 'vertical',
    outline: 'none',
    fontFamily: 'inherit',
    boxSizing: 'border-box',
  },
  actions: {
    display: 'flex',
    gap: '12px',
    marginTop: '24px',
  },
  skipButton: {
    flex: '1',
    padding: '12px',
    backgroundColor: 'transparent',
    border: '1px solid #333',
    borderRadius: '8px',
    color: '#888',
    fontSize: '0.85rem',
    cursor: 'pointer',
    fontWeight: '600',
  },
  submitButton: {
    flex: '2',
    padding: '12px',
    backgroundColor: '#a78bfa',
    border: 'none',
    borderRadius: '8px',
    color: '#000',
    fontSize: '0.85rem',
    cursor: 'pointer',
    fontWeight: '700',
    letterSpacing: '0.04em',
    textTransform: 'uppercase',
  },
};

export default MuscleGroupFeedbackPopup;
