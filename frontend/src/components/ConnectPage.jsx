import { useState } from 'react';
import { api } from '../services/api';

const DB_TYPES = ['sqlite', 'postgresql', 'mysql'];

export default function ConnectPage({ onConnected }) {
  const [dbType, setDbType] = useState('sqlite');
  const [form, setForm] = useState({
    database: './data/sample.db',
    host: 'localhost',
    port: '',
    username: '',
    password: '',
  });
  const [testing, setTesting] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const set = (key, val) => setForm(f => ({ ...f, [key]: val }));

  const getPayload = () => ({
    db_type: dbType,
    database: form.database,
    ...(dbType !== 'sqlite' && {
      host: form.host,
      port: form.port ? parseInt(form.port) : undefined,
      username: form.username || undefined,
      password: form.password || undefined,
    }),
  });

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.testConnection(getPayload());
      setTestResult({ success: res.success, msg: res.message });
    } catch (err) {
      setTestResult({ success: false, msg: err.message });
    } finally {
      setTesting(false);
    }
  };

  const handleConnect = async () => {
    setConnecting(true);
    setTestResult(null);
    try {
      const res = await api.connect(getPayload());
      setTestResult({ success: true, msg: res.message });
      if (onConnected) onConnected(res);
    } catch (err) {
      setTestResult({ success: false, msg: err.message });
    } finally {
      setConnecting(false);
    }
  };

  return (
    <div className="connect-page">
      <div className="connect-card">
        <div className="connect-title">Connect Database</div>
        <div className="connect-subtitle">
          Configure your database connection. Credentials are never stored in logs.
        </div>

        <div className="form-group">
          <label className="form-label">Database Type</label>
          <select className="form-select" value={dbType} onChange={e => setDbType(e.target.value)}>
            {DB_TYPES.map(t => <option key={t} value={t}>{t.toUpperCase()}</option>)}
          </select>
        </div>

        {dbType === 'sqlite' ? (
          <div className="form-group">
            <label className="form-label">Database File Path</label>
            <input className="form-input" type="text" value={form.database} onChange={e => set('database', e.target.value)} placeholder="./data/sample.db" />
          </div>
        ) : (
          <>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Host</label>
                <input className="form-input" type="text" value={form.host} onChange={e => set('host', e.target.value)} placeholder="localhost" />
              </div>
              <div className="form-group">
                <label className="form-label">Port</label>
                <input className="form-input" type="number" value={form.port} onChange={e => set('port', e.target.value)} placeholder={dbType === 'postgresql' ? '5432' : '3306'} />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Database Name</label>
              <input className="form-input" type="text" value={form.database} onChange={e => set('database', e.target.value)} placeholder="mydb" />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Username</label>
                <input className="form-input" type="text" value={form.username} onChange={e => set('username', e.target.value)} placeholder="postgres" />
              </div>
              <div className="form-group">
                <label className="form-label">Password</label>
                <input className="form-input" type="password" value={form.password} onChange={e => set('password', e.target.value)} placeholder="••••••••" />
              </div>
            </div>
          </>
        )}

        {testResult && (
          <div className={`test-result ${testResult.success ? 'success' : 'error'}`}>
            {testResult.success ? '✓ ' : '✗ '}{testResult.msg}
          </div>
        )}

        <div className="connect-actions">
          <button className="btn btn-secondary" onClick={handleTest} disabled={testing}>
            {testing ? 'Testing...' : 'Test Connection'}
          </button>
          <button className="btn btn-primary" onClick={handleConnect} disabled={connecting}>
            {connecting ? 'Connecting...' : 'Connect'}
          </button>
        </div>

        <div style={{ marginTop: '24px', padding: '14px', background: 'rgba(116,150,44,0.08)', border: '1px solid rgba(116,150,44,0.2)', borderRadius: 'var(--radius-md)' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-accent)', marginBottom: '6px' }}>
            Sample Database
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
            The sample SQLite database at <code style={{ color: 'var(--accent-secondary)' }}>./data/sample.db</code> is pre-loaded with 25,000 realistic orders, customers, products, employees, and payments.
          </div>
        </div>
      </div>
    </div>
  );
}
