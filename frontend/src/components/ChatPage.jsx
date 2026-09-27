import { useState, useRef, useEffect, useCallback } from 'react';
import { api } from '../services/api';

const EXAMPLE_QUERIES = [
  "What were the top 5 products by revenue in 2025?",
  "Show monthly revenue for 2025",
  "Which customers have never placed an order?",
  "Compare revenue between 2024 and 2025",
];

const LOADING_STEPS = [
  "🔍 Retrieving schema...",
  "🧠 Planning query...",
  "⚙️ Generating SQL...",
  "✅ Validating...",
  "🚀 Executing...",
  "📊 Analyzing results...",
];

export default function ChatPage({ sessionId, onHistoryUpdate }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const stepIntervalRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const startLoadingAnimation = () => {
    let step = 0;
    setLoadingStep(0);
    stepIntervalRef.current = setInterval(() => {
      step = Math.min(step + 1, LOADING_STEPS.length - 1);
      setLoadingStep(step);
    }, 1200);
  };

  const stopLoadingAnimation = () => {
    if (stepIntervalRef.current) {
      clearInterval(stepIntervalRef.current);
      stepIntervalRef.current = null;
    }
  };

  const handleSubmit = useCallback(async (question) => {
    const q = (question || input).trim();
    if (!q || loading) return;

    setInput('');
    setLoading(true);
    startLoadingAnimation();

    setMessages(prev => [...prev, { type: 'user', content: q }]);

    try {
      const result = await api.runQuery(q, sessionId);
      setMessages(prev => [...prev, { type: 'assistant', data: result }]);
      if (onHistoryUpdate) onHistoryUpdate();
    } catch (err) {
      setMessages(prev => [...prev, {
        type: 'error',
        content: err.message || 'An unexpected error occurred.'
      }]);
    } finally {
      stopLoadingAnimation();
      setLoading(false);
    }
  }, [input, loading, sessionId, onHistoryUpdate]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const autoResize = () => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = 'auto';
      ta.style.height = Math.min(ta.scrollHeight, 200) + 'px';
    }
  };

  return (
    <div className="chat-page">
      <div className="chat-container">
        {messages.length === 0 && !loading && (
          <WelcomeScreen onExample={handleSubmit} />
        )}

        {messages.map((msg, i) => (
          <div key={i} className="message-group">
            {msg.type === 'user' && (
              <div className="user-message">{msg.content}</div>
            )}
            {msg.type === 'assistant' && (
              <ResultCard data={msg.data} />
            )}
            {msg.type === 'error' && (
              <div style={{ color: 'var(--accent-error)', padding: '12px', background: '#fef2f2', border: '1px solid #f87171', borderRadius: '12px' }}>
                ⚠️ {msg.content}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="loading-box fade-in">
            <div className="spinner-dots">
              <div className="spinner-dot" />
              <div className="spinner-dot" />
              <div className="spinner-dot" />
            </div>
            <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
              {LOADING_STEPS[loadingStep]}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} style={{ height: '40px' }} />
      </div>

      <div className="query-input-wrapper">
        <div className="query-input-card">
          <span style={{ fontSize: '20px', color: 'var(--text-muted)', marginBottom: '10px' }}>📎</span>
          <textarea
            ref={textareaRef}
            className="query-textarea"
            value={input}
            onChange={e => { setInput(e.target.value); autoResize(); }}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your database..."
            rows={1}
            disabled={loading}
          />
          <button
            className="submit-btn"
            onClick={() => handleSubmit()}
            disabled={loading || !input.trim()}
          >
            ↑
          </button>
        </div>
      </div>
    </div>
  );
}

function WelcomeScreen({ onExample }) {
  return (
    <div className="welcome-screen fade-in">
      <div className="analyst-badge">
        <div className="dot" />
        Your personal data analyst
      </div>
      
      <div className="welcome-title">
        Data has a story.<br/><em>Let's find it.</em>
      </div>
      
      <div className="welcome-subtitle">
        Meet the AI agent that turns your database into sharp answers,
        meaningful visuals, and confident next steps.
      </div>
      
      <div style={{ display: 'flex', gap: '16px', marginTop: '12px' }}>
        <button className="btn-pill btn-pill-primary" onClick={() => onExample(EXAMPLE_QUERIES[0])}>
          Start analyzing free ➔
        </button>
        <button className="btn-pill btn-pill-secondary" onClick={() => alert('Demo only!')}>
          ▶ See how it works
        </button>
      </div>
      
      <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>
        ✓ No setup required &nbsp;·&nbsp; ✓ Your data stays yours
      </div>

      <div className="example-queries">
        {EXAMPLE_QUERIES.map((q, i) => (
          <button key={i} className="example-chip" onClick={() => onExample(q)}>
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

function ResultCard({ data }) {
  const [activeTab, setActiveTab] = useState('answer');

  if (!data) return null;

  const { status, answer, sql_output, execution, analytics, visualization, performance, planner } = data;

  const TABS = [
    { id: 'answer', label: '💬 Answer' },
    { id: 'data', label: `📋 Data (${execution?.row_count || 0})` },
    { id: 'chart', label: '📊 Chart' },
    { id: 'insights', label: '💡 Insights' },
    { id: 'sql', label: '🔧 SQL' },
    { id: 'performance', label: '⚡ Performance' },
  ];

  return (
    <div className="result-card fade-in">
      <div className="result-header">
        <div className="result-agent-badge">
          <div className="icon">✨</div>
          DataLens AI
        </div>
        <div className="result-time">
          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>

      <div className="result-tabs">
        {TABS.map(t => (
          <button
            key={t.id}
            className={`tab-btn ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="tab-content">
        {activeTab === 'answer' && (
          <div style={{ fontSize: '15px', lineHeight: '1.6', color: 'var(--text-primary)' }}>
            {status === 'error' ? (
              <span style={{ color: 'var(--accent-error)' }}>⚠️ {answer}</span>
            ) : status === 'no_results' ? (
              <span style={{ color: 'var(--text-muted)' }}>No matching records were found.</span>
            ) : (
              answer
            )}
          </div>
        )}
        
        {activeTab === 'data' && (
          <DataTab execution={execution} />
        )}
        
        {activeTab === 'chart' && (
          <ChartTab visualization={visualization} execution={execution} />
        )}
        
        {activeTab === 'insights' && (
          <InsightsTab analytics={analytics} />
        )}
        
        {activeTab === 'sql' && (
          <SQLTab sqlOutput={sql_output} />
        )}
        
        {activeTab === 'performance' && (
          <PerformanceTab performance={performance} />
        )}
      </div>
    </div>
  );
}

function SQLTab({ sqlOutput }) {
  if (!sqlOutput?.sql) return <div className="empty-state">No SQL generated.</div>;
  return (
    <div>
      <div className="sql-block">
        <div className="sql-block-header">
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Generated SQL</span>
        </div>
        <pre className="sql-code">{sqlOutput.sql}</pre>
      </div>
      {sqlOutput.explanation && (
        <div style={{ marginTop: '16px', fontSize: '14px', color: 'var(--text-secondary)' }}>
          <strong>Explanation:</strong> {sqlOutput.explanation}
        </div>
      )}
    </div>
  );
}

function DataTab({ execution }) {
  if (!execution?.columns?.length) return <div className="empty-state">No data returned.</div>;
  return (
    <div className="data-table-wrapper">
      <table className="data-table">
        <thead>
          <tr>{execution.columns.map((col, i) => <th key={i}>{col}</th>)}</tr>
        </thead>
        <tbody>
          {execution.rows.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td key={j}>{cell === null ? 'NULL' : String(cell)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ChartTab({ visualization, execution }) {
  const [RechartsLib, setRechartsLib] = useState(null);

  useEffect(() => {
    import('recharts').then(lib => setRechartsLib(lib));
  }, []);

  if (!visualization || visualization.chart_type === 'table') {
    return <div className="empty-state"><div className="empty-icon">📋</div><div className="empty-text">Best viewed as a table</div></div>;
  }
  
  if (!RechartsLib) return <div className="empty-state">Loading charts...</div>;

  const { ResponsiveContainer, LineChart, BarChart, PieChart, Line, Bar, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend } = RechartsLib;
  const data = visualization.data?.slice(0, 100) || [];
  const xKey = visualization.x_axis;
  const yKeys = visualization.y_axes || [visualization.y_axis];
  const COLORS = ['#1a3636', '#74962c', '#a9c67f', '#d6ebec'];

  const renderChart = () => {
    switch (visualization.chart_type) {
      case 'bar':
        return (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-subtle)" />
            <XAxis dataKey={xKey} tick={{ fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: 'var(--shadow-card)' }} />
            {yKeys.map((k, i) => <Bar key={k} dataKey={k} fill={COLORS[i % COLORS.length]} radius={[4, 4, 0, 0]} />)}
          </BarChart>
        );
      case 'line':
        return (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-subtle)" />
            <XAxis dataKey={xKey} tick={{ fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: 'var(--shadow-card)' }} />
            {yKeys.map((k, i) => <Line key={k} type="monotone" dataKey={k} stroke={COLORS[i % COLORS.length]} strokeWidth={3} dot={false} />)}
          </LineChart>
        );
      case 'pie':
        return (
          <PieChart>
            <Pie data={data} dataKey={visualization.y_axis} nameKey={xKey} cx="50%" cy="50%" outerRadius={120}>
              {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie>
            <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: 'var(--shadow-card)' }} />
          </PieChart>
        );
      default: return null;
    }
  };

  return (
    <div style={{ height: '350px', width: '100%' }}>
      <div style={{ marginBottom: '16px', fontWeight: 600, color: 'var(--text-secondary)' }}>{visualization.title}</div>
      <ResponsiveContainer width="100%" height="100%">
        {renderChart()}
      </ResponsiveContainer>
    </div>
  );
}

function InsightsTab({ analytics }) {
  if (!analytics?.insights?.length) return <div className="empty-state">No insights available.</div>;
  return (
    <div className="insights-grid">
      {analytics.insights.map((ins, i) => (
        <div key={i} className="insight-card">
          <span style={{ fontSize: '20px' }}>💡</span>
          <span style={{ fontSize: '14px', color: 'var(--text-primary)', lineHeight: '1.5' }}>{ins}</span>
        </div>
      ))}
      {analytics.trends?.map((trend, i) => (
        <div key={`t${i}`} className="insight-card">
          <span style={{ fontSize: '20px' }}>📈</span>
          <span style={{ fontSize: '14px', color: 'var(--text-primary)', lineHeight: '1.5' }}>{trend}</span>
        </div>
      ))}
    </div>
  );
}

function PerformanceTab({ performance }) {
  if (!performance) return <div className="empty-state">No performance data.</div>;
  return (
    <div style={{ display: 'flex', gap: '24px' }}>
      <div style={{ padding: '20px', background: '#f8fafc', borderRadius: '12px', flex: 1 }}>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', fontWeight: 600 }}>Total Time</div>
        <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text-primary)' }}>{performance.total_time_ms?.toFixed(0)}<span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>ms</span></div>
      </div>
      <div style={{ padding: '20px', background: '#f8fafc', borderRadius: '12px', flex: 1 }}>
        <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', fontWeight: 600 }}>Execution Time</div>
        <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text-primary)' }}>{performance.execution_time_ms?.toFixed(0)}<span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>ms</span></div>
      </div>
    </div>
  );
}
