import { useState, useEffect } from 'react';
import { api } from '../services/api';

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr + 'Z').getTime();
  const sec = Math.floor(diff / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return `${Math.floor(hr / 24)}d ago`;
}

export default function HistoryPage({ onRestore }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api.getHistory(100)
      .then(data => setHistory(data.items || []))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="history-page">
      <div className="page-header">
        <div className="page-title">Query History</div>
        <div className="page-subtitle">{history.length} queries stored in session</div>
      </div>

      <div className="history-list">
        {loading && (
          <div className="empty-state">
            <div className="spinner-dots" style={{ margin: '0 auto' }}>
              <div className="spinner-dot" /><div className="spinner-dot" /><div className="spinner-dot" />
            </div>
          </div>
        )}

        {!loading && history.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">📜</div>
            <div className="empty-text">No queries yet. Start asking questions!</div>
          </div>
        )}

        {history.map(item => (
          <div
            key={item.query_id}
            className="history-item"
            onClick={() => onRestore && onRestore(item.question)}
          >
            <div className={`history-status ${item.success ? 'success' : 'error'}`} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="history-question">{item.question}</div>
              <div className="history-sql">{item.sql}</div>
              <div className="history-meta">
                <span>⏱ {item.execution_time_ms?.toFixed(0)}ms</span>
                <span>📋 {item.row_count} rows</span>
                {item.retries > 0 && <span>🔄 {item.retries} retries</span>}
                <span>{timeAgo(item.timestamp)}</span>
              </div>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', flexShrink: 0 }}>
              {item.success ? '✓' : '✗'}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
