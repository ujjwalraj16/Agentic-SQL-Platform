/**
 * hooks/useQuery.js – React hook for running queries with loading/error state.
 */

import { useState, useCallback } from 'react';
import { api } from '../services/api';

export function useQuery() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const runQuery = useCallback(async (question, sessionId) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.runQuery(question, sessionId);
      setResult(data);
      return data;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { loading, error, result, runQuery, reset };
}
