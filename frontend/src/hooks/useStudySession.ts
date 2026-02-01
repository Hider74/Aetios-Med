import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import type { StudySession } from '../types/study';

export const useStudySession = (topicId: string) => {
  const [session, setSession] = useState<StudySession | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [isActive, setIsActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Timer effect
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | undefined;
    
    if (isActive && session) {
      interval = setInterval(() => {
        const now = new Date();
        const duration = Math.floor((now.getTime() - session.startTime.getTime()) / 1000 / 60);
        setElapsed(duration);
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isActive, session]);

  // Start study session
  const startSession = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const newSession = await api.startStudySession(topicId);
      setSession(newSession);
      setIsActive(true);
      setElapsed(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start session');
    } finally {
      setLoading(false);
    }
  }, [topicId]);

  // End study session
  const endSession = useCallback(async (
    quizzesTaken: number,
    quizzesCorrect: number,
    confidenceAfter: number,
    notes: string = ''
  ) => {
    if (!session) return;

    setLoading(true);
    setError(null);

    try {
      const updatedSession = await api.endStudySession(session.id, {
        duration: elapsed,
        quizzesTaken,
        quizzesCorrect,
        confidenceAfter,
        notes,
      });
      
      setSession(updatedSession);
      setIsActive(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to end session');
    } finally {
      setLoading(false);
    }
  }, [session, elapsed]);

  // Pause/Resume
  const togglePause = useCallback(() => {
    setIsActive(!isActive);
  }, [isActive]);

  // Format elapsed time
  const formatElapsed = useCallback(() => {
    const hours = Math.floor(elapsed / 60);
    const minutes = elapsed % 60;
    return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`;
  }, [elapsed]);

  return {
    session,
    elapsed,
    isActive,
    loading,
    error,
    startSession,
    endSession,
    togglePause,
    formatElapsed,
  };
};
