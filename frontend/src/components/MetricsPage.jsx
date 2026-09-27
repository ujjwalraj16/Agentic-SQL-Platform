import { useState, useEffect } from 'react';
import { api } from '../services/api';

const METRIC_CARDS = [
  { key: 'total_queries', label: 'Total Queries', icon: '🔢', format: v => v.toLocaleString() },
  { key: 'sql_success_rate', label: 'SQL Success Rate', icon: '✅', format: v => `${v}%` },
  { key: 'self_correction_rate', label: 'Self-Correction Rate', icon: '🔄', format: v => `${v}%` },
  { key: 'avg_latency_ms', label: 'Avg Latency', icon: '⚡', format: v => `${v.toFixed(0)}ms` },
  { key: 'avg_execution_time_ms', label: 'Avg Execution', icon: '🚀', format: v => `${v.toFixed(0)}ms` },
  { key: 'avg_retries', label: 'Avg Retries', icon: '🔁', format: v => v.toFixed(2) },
  { key: 'token_reduction_pct', label: 'Token Reduction', icon: '💰', format: v => `${v}%` },
  { key: 'estimated_cost_usd', label: 'Est. LLM Cost', icon: '💵', format: v => `$${v.toFixed(4)}` },
  { key: 'total_input_tokens', label: 'Input Tokens', icon: '📥', format: v => v.toLocaleString() },
  { key: 'total_output_tokens', label: 'Output Tokens', icon: '📤', format: v => v.toLocaleString() },
];

export default function MetricsPage() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = () => {
      api.getMetrics()
        .then(setMetrics)
        .catch(() => {})
        .finally(() => setLoading(false));
    };
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="metrics-page">
      <div className="page-header" style={{ marginBottom: '24px' }}>
        <div className="page-title">Evaluation Dashboard</div>
        <div className="page-subtitle">
          Real-time metrics computed from actual query logs — auto-refreshes every 10s
        </div>
      </div>

      {loading ? (
        <div className="empty-state">
          <div className="spinner-dots" style={{ margin: '0 auto' }}>
            <div className="spinner-dot" /><div className="spinner-dot" /><div className="spinner-dot" />
          </div>
        </div>
      ) : metrics?.total_queries === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📊</div>
          <div className="empty-text">Run some queries to see metrics here.</div>
        </div>
      ) : (
        <>
          <div className="metrics-grid">
            {METRIC_CARDS.map(card => (
              <div key={card.key} className="metric-card">
                <div className="metric-icon">{card.icon}</div>
                <div className="metric-label">{card.label}</div>
                <div className="metric-value">{metrics ? card.format(metrics[card.key] || 0) : '—'}</div>
              </div>
            ))}
          </div>

          {metrics && (
            <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-lg)', padding: '20px', marginTop: '8px' }}>
              <div style={{ fontSize: '14px', fontWeight: 700, marginBottom: '16px' }}>
                Token Efficiency (FAISS Schema Retrieval)
              </div>
              <div style={{ display: 'flex', gap: '16px', alignItems: 'center', marginBottom: '16px' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px' }}>
                    Avg tables retrieved vs total
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <div style={{ flex: 1, height: '8px', background: 'var(--bg-elevated)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{
                        height: '100%',
                        background: 'linear-gradient(90deg, #6366f1, #06b6d4)',
                        borderRadius: '4px',
                        width: metrics.schema_total_avg_tables > 0
                          ? `${(metrics.schema_retrieval_avg_tables / metrics.schema_total_avg_tables) * 100}%`
                          : '0%',
                        transition: 'width 0.8s ease',
                      }} />
                    </div>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-accent)', minWidth: '80px' }}>
                      {metrics.schema_retrieval_avg_tables.toFixed(1)} / {metrics.schema_total_avg_tables.toFixed(1)} tables
                    </span>
                  </div>
                </div>
                <div style={{ textAlign: 'center', padding: '12px 20px', background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text-accent)' }}>
                    {metrics.token_reduction_pct}%
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>token savings</div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div style={{ padding: '12px', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Mode A (Full Schema)</div>
                  <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Sends all {metrics.schema_total_avg_tables.toFixed(0)} tables to LLM</div>
                </div>
                <div style={{ padding: '12px', background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>Mode B (FAISS Retrieval) ✓</div>
                  <div style={{ fontSize: '13px', color: 'var(--text-accent)' }}>Sends only {metrics.schema_retrieval_avg_tables.toFixed(1)} relevant tables</div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
