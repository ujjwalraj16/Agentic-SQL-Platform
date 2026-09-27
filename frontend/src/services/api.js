/**
 * services/api.js – Centralized API client for the Agentic SQL Intelligence Platform.
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(method, path, body = null) {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) options.body = JSON.stringify(body);

  const res = await fetch(`${BASE_URL}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Health
  health: () => request('GET', '/health'),

  // Database
  testConnection: (data) => request('POST', '/api/database/test', data),
  connect: (data) => request('POST', '/api/database/connect', data),

  // Schema
  getSchema: () => request('GET', '/api/schema'),

  // Query
  runQuery: (question, sessionId) =>
    request('POST', '/api/query', { question, session_id: sessionId }),

  // Optimization
  optimizeQuery: (sql) => request('POST', '/api/query/optimize', { sql }),

  // History
  getHistory: (limit = 50) => request('GET', `/api/history?limit=${limit}`),
  getQueryById: (id) => request('GET', `/api/history/${id}`),

  // Metrics
  getMetrics: () => request('GET', '/api/metrics'),
};
