import { useState, useEffect, useCallback } from 'react';
import ChatPage from './components/ChatPage';
import SchemaPage from './components/SchemaPage';
import HistoryPage from './components/HistoryPage';
import MetricsPage from './components/MetricsPage';
import ConnectPage from './components/ConnectPage';
import { api } from './services/api';
import './App.css';

const NAV_ITEMS = [
  { id: 'chat', label: 'Analysis Chat' },
  { id: 'schema', label: 'Schema' },
  { id: 'history', label: 'History' },
  { id: 'metrics', label: 'Capabilities' },
];

const SESSION_ID = `session_${Date.now()}`;

export default function App() {
  const [activePage, setActivePage] = useState('chat');
  const [dbStatus, setDbStatus] = useState({ connected: false, name: '', type: '' });
  const [historyCount, setHistoryCount] = useState(0);
  const [restoreQuery, setRestoreQuery] = useState(null);

  useEffect(() => {
    api.health()
      .then(data => {
        setDbStatus({
          connected: data.db_connected,
          name: 'sample.db',
          type: data.db_type || 'sqlite',
        });
      })
      .catch(() => {
        setDbStatus({ connected: false, name: 'Not connected', type: '' });
      });
  }, []);

  const handleHistoryUpdate = useCallback(() => {
    setHistoryCount(n => n + 1);
  }, []);

  const handleRestoreQuery = useCallback((question) => {
    setRestoreQuery(question);
    setActivePage('chat');
    setTimeout(() => setRestoreQuery(null), 100);
  }, []);

  const handleConnected = useCallback((info) => {
    setDbStatus({
      connected: true,
      name: info.database || 'database',
      type: info.db_type || 'sqlite',
    });
    setActivePage('chat');
  }, []);

  return (
    <div className="app-layout">
      {/* Top Navigation */}
      <nav className="top-nav">
        <div className="nav-left">
          <div className="logo-container" onClick={() => setActivePage('chat')}>
            <div className="logo-icon">✨</div>
            <div className="logo-text">DataLens</div>
          </div>
        </div>

        <div className="nav-center">
          {NAV_ITEMS.map(item => (
            <div
              key={item.id}
              className={`nav-link ${activePage === item.id ? 'active' : ''}`}
              onClick={() => setActivePage(item.id)}
            >
              {item.label}
            </div>
          ))}
        </div>

        <div className="nav-right">
          <div style={{ fontSize: '12px', fontWeight: 500, color: 'var(--text-muted)' }}>
            {dbStatus.connected ? (
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-success)' }}></span>
                {dbStatus.type.toUpperCase()}: {dbStatus.name}
              </span>
            ) : (
              <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent-error)' }}></span>
                No dataset loaded
              </span>
            )}
          </div>
          <button 
            className={`btn-pill ${activePage === 'connect' ? 'btn-pill-primary' : 'btn-pill-secondary'}`}
            onClick={() => setActivePage('connect')}
          >
            Connect DB ➔
          </button>
        </div>
      </nav>

      {/* Main content */}
      <main className="main-content">
        {activePage === 'chat' && (
          <ChatPage
            sessionId={SESSION_ID}
            onHistoryUpdate={handleHistoryUpdate}
            initialQuery={restoreQuery}
          />
        )}
        {activePage === 'schema' && <SchemaPage />}
        {activePage === 'history' && (
          <HistoryPage onRestore={handleRestoreQuery} />
        )}
        {activePage === 'metrics' && <MetricsPage />}
        {activePage === 'connect' && (
          <ConnectPage onConnected={handleConnected} />
        )}
      </main>
    </div>
  );
}
