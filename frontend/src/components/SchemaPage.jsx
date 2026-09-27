import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function SchemaPage() {
  const [schema, setSchema] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTable, setSelectedTable] = useState(null);

  useEffect(() => {
    api.getSchema()
      .then(data => {
        setSchema(data);
        if (data.tables?.length > 0) setSelectedTable(data.tables[0]);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="schema-page">
      <div className="page-header">
        <div className="page-title">Schema Explorer</div>
      </div>
      <div className="empty-state">
        <div className="spinner-dots" style={{ margin: '0 auto' }}>
          <div className="spinner-dot" /><div className="spinner-dot" /><div className="spinner-dot" />
        </div>
      </div>
    </div>
  );

  if (error) return (
    <div className="schema-page">
      <div className="page-header"><div className="page-title">Schema Explorer</div></div>
      <div className="error-message" style={{ margin: '20px' }}>
        <span>⚠️</span><span>{error}</span>
      </div>
    </div>
  );

  return (
    <div className="schema-page">
      <div className="page-header">
        <div className="page-title">Schema Explorer</div>
        <div className="page-subtitle">
          {schema?.database} · {schema?.db_type?.toUpperCase()} · {schema?.total_tables} tables
        </div>
      </div>

      <div className="schema-layout">
        {/* Table List */}
        <div className="schema-sidebar">
          <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px', padding: '0 4px' }}>
            Tables
          </div>
          {schema?.tables?.map(tbl => (
            <div
              key={tbl.name}
              className={`table-list-item ${selectedTable?.name === tbl.name ? 'active' : ''}`}
              onClick={() => setSelectedTable(tbl)}
            >
              <span>🗃️</span>
              <span>{tbl.name}</span>
              <span className="table-count">{tbl.row_count?.toLocaleString()}</span>
            </div>
          ))}
        </div>

        {/* Table Detail */}
        <div className="schema-main">
          {selectedTable ? (
            <div className="table-detail">
              <div className="table-detail-header">
                <span style={{ fontSize: '20px' }}>🗃️</span>
                <div className="table-detail-title">{selectedTable.name}</div>
                <div className="table-detail-count">{selectedTable.row_count?.toLocaleString()} rows</div>
                <div style={{ marginLeft: 'auto', fontSize: '12px', color: 'var(--text-muted)' }}>
                  {selectedTable.columns?.length} columns
                </div>
              </div>

              <div className="column-list">
                {selectedTable.columns?.map(col => (
                  <div key={col.name} className="column-row">
                    <div className="col-name">{col.name}</div>
                    <div className="col-type">{col.type}</div>
                    <div className="col-badges">
                      {col.primary_key && <span className="badge badge-pk">PK</span>}
                      {col.foreign_key && <span className="badge badge-fk">FK</span>}
                      {!col.nullable && <span className="badge" style={{ background: 'rgba(239,68,68,0.15)', color: '#fca5a5' }}>NOT NULL</span>}
                    </div>
                    {col.foreign_key && (
                      <div className="col-fk-ref">→ {col.foreign_key}</div>
                    )}
                    {col.sample_values?.length > 0 && (
                      <div style={{ marginLeft: 'auto', fontSize: '11px', color: 'var(--text-muted)' }}>
                        e.g. {col.sample_values.slice(0, 2).map(String).join(', ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {selectedTable.relationships?.length > 0 && (
                <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border-subtle)' }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Relationships
                  </div>
                  {selectedTable.relationships.map((r, i) => (
                    <div key={i} style={{ fontSize: '12px', color: 'var(--text-secondary)', padding: '4px 0', fontFamily: 'monospace' }}>
                      {r}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">🗃️</div>
              <div className="empty-text">Select a table to explore</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
