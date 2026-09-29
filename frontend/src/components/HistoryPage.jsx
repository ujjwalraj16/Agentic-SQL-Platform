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

  const handleClear = async () => {
    try {
      await api.clearHistory();
      setHistory([]);
    } catch (e) {
      console.error('Failed to clear history:', e);
    }
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation(); // prevent restore query click
    try {
      await api.deleteHistoryItem(id);
      setHistory(prev => prev.filter(item => item.query_id !== id));
    } catch (e) {
      console.error('Failed to delete item:', e);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="history-page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div className="page-title">Query History</div>
          <div className="page-subtitle">{history.length} queries stored in session</div>
        </div>
        {history.length > 0 && (
          <button 
            className="btn btn-secondary" 
            onClick={handleClear}
            style={{ padding: '6px 12px', fontSize: '12px', flex: 'none', height: 'fit-content' }}
          >
            Clear History
          </button>
        )}
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
            <div style={{ opacity: 0.4 }}>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
            </div>
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
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', justifyContent: 'space-between' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                {item.success ? '✓' : '✗'}
              </div>
              <button 
                className="btn btn-secondary" 
                onClick={(e) => handleDelete(e, item.query_id)}
                style={{ padding: '4px 8px', fontSize: '10px', marginTop: '8px', flex: 'none', height: 'fit-content' }}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
