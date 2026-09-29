import { useState, useRef, useEffect, useCallback } from 'react';
import { api } from '../services/api';

// ── SVG Icons ─────────────────────────────────────────────────────────────────
const Icon = {
  Search:       () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>),
  Brain:        () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-1.98-3 2.5 2.5 0 0 1-1.32-4.24 3 3 0 0 1 .34-5.58 2.5 2.5 0 0 1 1.32-4.24A2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 1.98-3 2.5 2.5 0 0 0 1.32-4.24 3 3 0 0 0-.34-5.58 2.5 2.5 0 0 0-1.32-4.24A2.5 2.5 0 0 0 14.5 2Z"/></svg>),
  Code:         () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>),
  Check:        () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>),
  Play:         () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><polygon points="6 3 20 12 6 21 6 3"/></svg>),
  BarChart:     () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" x2="18" y1="20" y2="10"/><line x1="12" x2="12" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="14"/><line x1="2" x2="22" y1="20" y2="20"/></svg>),
  MessageSq:    () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>),
  Table:        () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3v18M3 9h18M3 15h18"/><rect width="18" height="18" x="3" y="3" rx="2"/></svg>),
  Lightbulb:    () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>),
  Terminal:     () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" x2="20" y1="19" y2="19"/></svg>),
  Zap:          () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/></svg>),
  Sparkle:      () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/></svg>),
  TrendUp:      () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>),
  Warning:      () => (<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>),
  Paperclip:    () => (<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>),
};

const PALETTE = ['#1a3636', '#74962c', '#a9c67f', '#2d7d7d', '#c4a23d', '#5b7fa6', '#d6ebec', '#8b5e3c'];

const EXAMPLE_QUERIES = [
  "What were the top 5 products by revenue in 2025?",
  "Show monthly revenue for 2025",
  "Which customers have never placed an order?",
  "Compare revenue between 2024 and 2025",
];

const LOADING_STEPS = [
  { icon: Icon.Search,   label: "Retrieving schema..." },
  { icon: Icon.Brain,    label: "Planning query..." },
  { icon: Icon.Code,     label: "Generating SQL..." },
  { icon: Icon.Check,    label: "Validating..." },
  { icon: Icon.Play,     label: "Executing..." },
  { icon: Icon.BarChart, label: "Analyzing results..." },
];

const TABS = [
  { id: 'answer',      label: 'Answer',      Ico: Icon.MessageSq },
  { id: 'data',        label: 'Data',        Ico: Icon.Table     },
  { id: 'chart',       label: 'Chart',       Ico: Icon.BarChart  },
  { id: 'insights',    label: 'Insights',    Ico: Icon.Lightbulb },
  { id: 'sql',         label: 'SQL',         Ico: Icon.Terminal  },
  { id: 'performance', label: 'Performance', Ico: Icon.Zap       },
];

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function ChatPage({ sessionId, onHistoryUpdate, onConnectDB }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const stepIntervalRef = useRef(null);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

  const startLoadingAnimation = () => {
    let step = 0; setLoadingStep(0);
    stepIntervalRef.current = setInterval(() => { step = Math.min(step + 1, LOADING_STEPS.length - 1); setLoadingStep(step); }, 1200);
  };
  const stopLoadingAnimation = () => { if (stepIntervalRef.current) { clearInterval(stepIntervalRef.current); stepIntervalRef.current = null; } };

  const handleSubmit = useCallback(async (question) => {
    const q = (question || input).trim();
    if (!q || loading) return;
    setInput(''); setLoading(true); startLoadingAnimation();
    setMessages(prev => [...prev, { type: 'user', content: q }]);
    try {
      const result = await api.runQuery(q, sessionId);
      setMessages(prev => [...prev, { type: 'assistant', data: result }]);
      if (onHistoryUpdate) onHistoryUpdate();
    } catch (err) {
      setMessages(prev => [...prev, { type: 'error', content: err.message || 'An unexpected error occurred.' }]);
    } finally { stopLoadingAnimation(); setLoading(false); }
  }, [input, loading, sessionId, onHistoryUpdate]);

  const handleKeyDown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); } };
  const autoResize = () => { const ta = textareaRef.current; if (ta) { ta.style.height = 'auto'; ta.style.height = Math.min(ta.scrollHeight, 200) + 'px'; } };
  const StepIcon = LOADING_STEPS[loadingStep]?.icon;

  return (
    <div className="chat-page">
      <div className="chat-container">
        {messages.length === 0 && !loading && <WelcomeScreen onExample={handleSubmit} onConnectDB={onConnectDB} />}
        {messages.map((msg, i) => (
          <div key={i} className="message-group">
            {msg.type === 'user' && <div className="user-message">{msg.content}</div>}
            {msg.type === 'assistant' && <ResultCard data={msg.data} />}
            {msg.type === 'error' && (
              <div style={{ color:'var(--accent-error)', padding:'12px', background:'#fef2f2', border:'1px solid #f87171', borderRadius:'12px', display:'flex', alignItems:'center', gap:'8px' }}>
                <Icon.Warning /> {msg.content}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="loading-box fade-in">
            <div className="spinner-dots"><div className="spinner-dot"/><div className="spinner-dot"/><div className="spinner-dot"/></div>
            <div style={{ fontSize:'14px', color:'var(--text-secondary)', display:'flex', alignItems:'center', gap:'6px' }}>
              {StepIcon && <StepIcon />}{LOADING_STEPS[loadingStep]?.label}
            </div>
          </div>
        )}
        <div ref={messagesEndRef} style={{ height: '40px' }} />
      </div>
      <div className="query-input-wrapper">
        <div className="query-input-card">
          <span style={{ color:'var(--text-muted)', marginBottom:'10px', display:'flex' }}><Icon.Paperclip /></span>
          <textarea ref={textareaRef} className="query-textarea" value={input}
            onChange={e => { setInput(e.target.value); autoResize(); }}
            onKeyDown={handleKeyDown} placeholder="Ask a question about your database..." rows={1} disabled={loading} />
          <button className="submit-btn" onClick={() => handleSubmit()} disabled={loading || !input.trim()}>&#x2191;</button>
        </div>
      </div>
    </div>
  );
}

// ── Welcome ───────────────────────────────────────────────────────────────────
function WelcomeScreen({ onExample, onConnectDB }) {
  return (
    <div className="welcome-screen fade-in">
      <div className="analyst-badge"><div className="dot" />Your personal data analyst</div>
      <div className="welcome-title">Data has a story.<br/><em>Let's find it.</em></div>
      <div className="welcome-subtitle">
        Connect your own database or use the built-in demo. Ask questions in plain English
        and get instant SQL, charts, and business insights.
      </div>
      <div style={{ display:'flex', gap:'16px', marginTop:'12px' }}>
        <button className="btn-pill btn-pill-primary" onClick={() => onExample(EXAMPLE_QUERIES[0])}>Try a demo query &#x2192;</button>
        <button className="btn-pill btn-pill-secondary" onClick={onConnectDB}>Connect your DB</button>
      </div>
      <div style={{ fontSize:'12px', color:'var(--text-muted)', marginTop:'8px' }}>&#x2713; Works with SQLite, PostgreSQL, MySQL &nbsp;&middot;&nbsp; &#x2713; Read-only &amp; secure</div>
      <div className="example-queries">
        {EXAMPLE_QUERIES.map((q, i) => <button key={i} className="example-chip" onClick={() => onExample(q)}>{q}</button>)}
      </div>
    </div>
  );
}

// ── Result Card ───────────────────────────────────────────────────────────────
function ResultCard({ data }) {
  const [activeTab, setActiveTab] = useState('answer');
  if (!data) return null;
  const { status, answer, sql_output, execution, analytics, visualization, performance } = data;
  return (
    <div className="result-card fade-in">
      <div className="result-header">
        <div className="result-agent-badge">
          <div className="icon" style={{ display:'flex', alignItems:'center' }}><Icon.Sparkle /></div>DataLens AI
        </div>
        <div className="result-time">{new Date().toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' })}</div>
      </div>
      <div className="result-tabs">
        {TABS.map(t => (
          <button key={t.id} className={`tab-btn ${activeTab === t.id ? 'active' : ''}`} onClick={() => setActiveTab(t.id)}>
            <span style={{ display:'flex', alignItems:'center', gap:'5px' }}>
              <t.Ico />{t.id === 'data' ? `Data (${execution?.row_count ?? 0})` : t.label}
            </span>
          </button>
        ))}
      </div>
      <div className="tab-content">
        {activeTab === 'answer' && (
          <div style={{ fontSize:'15px', lineHeight:'1.6', color:'var(--text-primary)' }}>
            {status === 'error' ? (
              <span style={{ color:'var(--accent-error)', display:'flex', alignItems:'flex-start', gap:'8px' }}><Icon.Warning />{answer}</span>
            ) : status === 'no_results' ? (
              <span style={{ color:'var(--text-muted)' }}>No matching records were found.</span>
            ) : answer}
          </div>
        )}
        {activeTab === 'data'        && <DataTab execution={execution} />}
        {activeTab === 'chart'       && <ChartTab visualization={visualization} />}
        {activeTab === 'insights'    && <InsightsTab analytics={analytics} />}
        {activeTab === 'sql'         && <SQLTab sqlOutput={sql_output} />}
        {activeTab === 'performance' && <PerformanceTab performance={performance} />}
      </div>
    </div>
  );
}

// ── SQL Tab ───────────────────────────────────────────────────────────────────
function SQLTab({ sqlOutput }) {
  if (!sqlOutput?.sql) return <div className="empty-state">No SQL generated.</div>;
  return (
    <div>
      <div className="sql-block">
        <div className="sql-block-header"><span style={{ fontSize:'12px', fontWeight:600, color:'var(--text-muted)', textTransform:'uppercase' }}>Generated SQL</span></div>
        <pre className="sql-code">{sqlOutput.sql}</pre>
      </div>
      {sqlOutput.explanation && <div style={{ marginTop:'16px', fontSize:'14px', color:'var(--text-secondary)' }}><strong>Explanation:</strong> {sqlOutput.explanation}</div>}
    </div>
  );
}

// ── Data Tab ──────────────────────────────────────────────────────────────────
function DataTab({ execution }) {
  if (!execution?.columns?.length) return <div className="empty-state">No data returned.</div>;
  return (
    <div className="data-table-wrapper">
      <table className="data-table">
        <thead><tr>{execution.columns.map((col, i) => <th key={i}>{col}</th>)}</tr></thead>
        <tbody>{execution.rows.map((row, i) => (
          <tr key={i}>{row.map((cell, j) => <td key={j}>{cell === null ? 'NULL' : String(cell)}</td>)}</tr>
        ))}</tbody>
      </table>
    </div>
  );
}

// ── Chart Tab ─────────────────────────────────────────────────────────────────
function ChartTab({ visualization }) {
  const [lib, setLib] = useState(null);
  useEffect(() => { import('recharts').then(m => setLib(m)); }, []);

  if (!visualization || visualization.chart_type === 'table') {
    return <EmptyState icon={<Icon.Table />} text="This result is best viewed as a table — check the Data tab." />;
  }
  if (!lib) return <div className="empty-state">Loading chart...</div>;

  const {
    ResponsiveContainer, BarChart, LineChart, PieChart, ScatterChart,
    Bar, Line, Pie, Cell, Scatter, XAxis, YAxis, ZAxis,
    CartesianGrid, Tooltip, Legend,
  } = lib;

  const raw   = visualization.data || [];
  const data  = raw.slice(0, 200);
  const xKey  = visualization.x_axis;
  const yKeys = (visualization.y_axes?.length ? visualization.y_axes : [visualization.y_axis]).filter(Boolean);

  const tooltipStyle = { borderRadius:'8px', border:'none', boxShadow:'0 4px 20px rgba(0,0,0,0.12)', fontSize:'13px' };
  const axisProps = { tick:{ fill:'var(--text-muted)', fontSize:12 }, axisLine:false, tickLine:false };

  // ── Render helpers ──────────────────────────────────────────────────────────
  const renderBar = () => (
    <BarChart data={data} margin={{ top:8, right:16, left:0, bottom:8 }}>
      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
      <XAxis dataKey={xKey} {...axisProps} interval="preserveStartEnd" />
      <YAxis {...axisProps} width={60} />
      <Tooltip contentStyle={tooltipStyle} />
      <Legend />
      {yKeys.map((k, i) => <Bar key={k} dataKey={k} fill={PALETTE[i % PALETTE.length]} radius={[4,4,0,0]} maxBarSize={60} />)}
    </BarChart>
  );

  const renderLine = () => (
    <LineChart data={data} margin={{ top:8, right:16, left:0, bottom:8 }}>
      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
      <XAxis dataKey={xKey} {...axisProps} interval="preserveStartEnd" />
      <YAxis {...axisProps} width={60} />
      <Tooltip contentStyle={tooltipStyle} />
      <Legend />
      {yKeys.map((k, i) => (
        <Line key={k} type="monotone" dataKey={k} stroke={PALETTE[i % PALETTE.length]}
          strokeWidth={2.5} dot={{ r:3 }} activeDot={{ r:5 }} />
      ))}
    </LineChart>
  );

  const renderPie = () => (
    <PieChart margin={{ top:8, right:16, left:0, bottom:8 }}>
      <Pie data={data} dataKey={yKeys[0]} nameKey={xKey} cx="50%" cy="48%"
        outerRadius="70%" innerRadius="35%"
        label={({ name, percent }) => percent > 0.04 ? `${name} ${(percent*100).toFixed(0)}%` : ''}>
        {data.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
      </Pie>
      <Tooltip contentStyle={tooltipStyle} formatter={(v) => [Number(v).toLocaleString(), yKeys[0]]} />
      <Legend />
    </PieChart>
  );

  const renderScatter = () => (
    <ScatterChart margin={{ top:8, right:16, left:0, bottom:8 }}>
      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
      <XAxis dataKey={xKey} name={xKey} {...axisProps} width={60} />
      <YAxis dataKey={yKeys[0]} name={yKeys[0]} {...axisProps} width={60} />
      <ZAxis range={[40, 200]} />
      <Tooltip contentStyle={tooltipStyle} cursor={{ strokeDasharray:'3 3' }} />
      <Legend />
      <Scatter data={data} fill={PALETTE[0]} opacity={0.7} />
    </ScatterChart>
  );

  // histogram: use BarChart treating the x-axis value as bins
  const renderHistogram = () => (
    <BarChart data={data} margin={{ top:8, right:16, left:0, bottom:8 }}>
      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
      <XAxis dataKey={xKey} {...axisProps} />
      <YAxis {...axisProps} width={60} />
      <Tooltip contentStyle={tooltipStyle} />
      <Bar dataKey={yKeys[0] || xKey} fill={PALETTE[0]} radius={[2,2,0,0]} />
    </BarChart>
  );

  // area variant using LineChart with filled area
  const renderArea = () => (
    <LineChart data={data} margin={{ top:8, right:16, left:0, bottom:8 }}>
      <defs>
        {yKeys.map((k, i) => (
          <linearGradient key={k} id={`grad-${i}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={PALETTE[i % PALETTE.length]} stopOpacity={0.3}/>
            <stop offset="95%" stopColor={PALETTE[i % PALETTE.length]} stopOpacity={0}/>
          </linearGradient>
        ))}
      </defs>
      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
      <XAxis dataKey={xKey} {...axisProps} interval="preserveStartEnd" />
      <YAxis {...axisProps} width={60} />
      <Tooltip contentStyle={tooltipStyle} />
      <Legend />
      {yKeys.map((k, i) => (
        <Line key={k} type="monotone" dataKey={k} stroke={PALETTE[i % PALETTE.length]}
          strokeWidth={2.5} dot={false} fill={`url(#grad-${i})`} />
      ))}
    </LineChart>
  );

  // Guard: need data + x/y keys for most chart types
  const type = visualization.chart_type;
  if (!data.length) return <EmptyState icon={<Icon.BarChart />} text="No data available to chart." />;
  if (!xKey && type !== 'histogram') return <EmptyState icon={<Icon.BarChart />} text="Chart configuration incomplete — missing axis data." />;

  const chartMap = {
    bar:       renderBar,
    line:      renderLine,
    pie:       renderPie,
    scatter:   renderScatter,
    histogram: renderHistogram,
    area:      renderArea,
  };

  const renderFn = chartMap[type];
  if (!renderFn) {
    return <EmptyState icon={<Icon.BarChart />} text={`Chart type "${type}" is not yet supported. Check the Data tab.`} />;
  }

  return (
    <div>
      {visualization.title && (
        <div style={{ marginBottom:'12px', fontWeight:600, fontSize:'14px', color:'var(--text-secondary)' }}>
          {visualization.title}
        </div>
      )}
      <div style={{ width:'100%', height:340 }}>
        <ResponsiveContainer width="100%" height="100%">
          {renderFn()}
        </ResponsiveContainer>
      </div>
      <div style={{ marginTop:'8px', fontSize:'12px', color:'var(--text-muted)', textAlign:'right' }}>
        {data.length} data point{data.length !== 1 ? 's' : ''} &middot; {type} chart
      </div>
    </div>
  );
}

function EmptyState({ icon, text }) {
  return (
    <div className="empty-state">
      <div style={{ display:'flex', justifyContent:'center', marginBottom:'8px', opacity:0.4 }}>{icon}</div>
      <div className="empty-text">{text}</div>
    </div>
  );
}

// ── Insights Tab ──────────────────────────────────────────────────────────────
function InsightsTab({ analytics }) {
  if (!analytics?.insights?.length && !analytics?.trends?.length)
    return <div className="empty-state">No insights available.</div>;
  return (
    <div className="insights-grid">
      {analytics.insights?.map((ins, i) => (
        <div key={i} className="insight-card">
          <span style={{ display:'flex', color:'var(--accent-primary)', flexShrink:0 }}><Icon.Lightbulb /></span>
          <span style={{ fontSize:'14px', color:'var(--text-primary)', lineHeight:'1.5' }}>{ins}</span>
        </div>
      ))}
      {analytics.trends?.map((trend, i) => (
        <div key={`t${i}`} className="insight-card">
          <span style={{ display:'flex', color:'#74962c', flexShrink:0 }}><Icon.TrendUp /></span>
          <span style={{ fontSize:'14px', color:'var(--text-primary)', lineHeight:'1.5' }}>{trend}</span>
        </div>
      ))}
    </div>
  );
}

// ── Performance Tab ───────────────────────────────────────────────────────────
function PerformanceTab({ performance }) {
  if (!performance) return <div className="empty-state">No performance data.</div>;
  const stats = [
    { label:'Total Time',     value:performance.total_time_ms?.toFixed(0),     unit:'ms' },
    { label:'Execution Time', value:performance.execution_time_ms?.toFixed(0), unit:'ms' },
    { label:'Retries',        value:performance.retries ?? 0,                  unit:''   },
    { label:'Tables Used',    value:performance.schema_tables_retrieved ?? 0,  unit:''   },
  ];
  return (
    <div style={{ display:'flex', gap:'16px', flexWrap:'wrap' }}>
      {stats.map(s => (
        <div key={s.label} style={{ padding:'20px', background:'#f8fafc', borderRadius:'12px', flex:'1 1 120px' }}>
          <div style={{ fontSize:'12px', color:'var(--text-muted)', marginBottom:'8px', textTransform:'uppercase', fontWeight:600 }}>{s.label}</div>
          <div style={{ fontSize:'28px', fontWeight:800, color:'var(--text-primary)' }}>
            {s.value}<span style={{ fontSize:'14px', color:'var(--text-muted)' }}>{s.unit}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
