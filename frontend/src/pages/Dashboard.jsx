import { useEffect, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

const statusLabels = {
  pending: 'Pending',
  flagged: 'Flagged',
  approved: 'Approved',
  rejected: 'Rejected',
  locked: 'Locked'
}

const sourceLabels = {
  sap: 'SAP',
  utility: 'Utility',
  travel: 'Travel'
}

function formatNumber(value, options = {}) {
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 1, ...options }).format(Number(value || 0))
}

function formatDate(value) {
  return value ? new Date(value).toLocaleDateString('en-GB', { month: 'short', day: 'numeric', year: 'numeric' }) : 'n/a'
}

function badgeClass(status) {
  return `badge badge-${status}`
}

async function fetchJson(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Request failed with status ${response.status}`)
  }

  return response.json()
}

export default function Dashboard() {
  const [tenants, setTenants] = useState([])
  const [tenantSlug, setTenantSlug] = useState('')
  const [dashboard, setDashboard] = useState(null)
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [savingId, setSavingId] = useState(null)
  const [error, setError] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [selectedId, setSelectedId] = useState(null)

  useEffect(() => {
    let active = true

    async function loadTenants() {
      try {
        const data = await fetchJson('/tenants/')
        if (!active) {
          return
        }
        setTenants(data)
        setTenantSlug((current) => current || data[0]?.slug || '')
      } catch (err) {
        if (active) {
          setError(err.message)
        }
      }
    }

    loadTenants()

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (!tenantSlug) {
      return
    }

    let active = true
    const controller = new AbortController()

    async function loadDashboard() {
      setLoading(true)
      setError('')

      const params = new URLSearchParams({ tenant: tenantSlug })
      if (statusFilter !== 'all') {
        params.set('status', statusFilter)
      }
      if (sourceFilter !== 'all') {
        params.set('source_type', sourceFilter)
      }
      if (search.trim()) {
        params.set('search', search.trim())
      }

      try {
        const [dashboardResponse, recordsResponse] = await Promise.all([
          fetchJson(`/dashboard/?tenant=${encodeURIComponent(tenantSlug)}`, { signal: controller.signal }),
          fetchJson(`/records/?${params.toString()}`, { signal: controller.signal })
        ])

        if (!active) {
          return
        }

        setDashboard(dashboardResponse)
        setRecords(recordsResponse.results || [])
        setSelectedId((current) => current || recordsResponse.results?.[0]?.id || null)
      } catch (err) {
        if (active && err.name !== 'AbortError') {
          setError('Unable to load the review dashboard. Make sure the Django API is running on port 8000.')
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    loadDashboard()

    return () => {
      active = false
      controller.abort()
    }
  }, [tenantSlug, statusFilter, sourceFilter, search])

  const selectedRecord = records.find((record) => record.id === selectedId) || dashboard?.latest_records?.[0] || dashboard?.queue?.[0] || null

  async function updateRecord(recordId, reviewStatus) {
    setSavingId(recordId)
    setError('')

    try {
      await fetchJson(`/records/${recordId}/`, {
        method: 'PATCH',
        body: JSON.stringify({
          review_status: reviewStatus,
          edited_by_name: 'Analyst'
        })
      })

      const params = new URLSearchParams({ tenant: tenantSlug })
      if (statusFilter !== 'all') {
        params.set('status', statusFilter)
      }
      if (sourceFilter !== 'all') {
        params.set('source_type', sourceFilter)
      }
      if (search.trim()) {
        params.set('search', search.trim())
      }

      const [dashboardResponse, recordsResponse] = await Promise.all([
        fetchJson(`/dashboard/?tenant=${encodeURIComponent(tenantSlug)}`),
        fetchJson(`/records/?${params.toString()}`)
      ])

      setDashboard(dashboardResponse)
      setRecords(recordsResponse.results || [])
      setSelectedId(recordId)
    } catch (err) {
      setError('Could not save the review decision.')
    } finally {
      setSavingId(null)
    }
  }

  return (
    <div className="app-shell">
      <div className="background-orb orb-a" />
      <div className="background-orb orb-b" />

      <main className="dashboard">
        <header className="hero">
          <div>
            <p className="eyebrow">Breathe ESG review center</p>
            <h1>Normalize messy source data, then let analysts sign off before audit.</h1>
            <p className="hero-copy">
              This prototype handles SAP exports, utility portal data, and Concur-style travel feeds with one review queue and a linked audit trail.
            </p>
          </div>

          <div className="hero-meta">
            <label className="field-label" htmlFor="tenant-select">Tenant</label>
            <select id="tenant-select" value={tenantSlug} onChange={(event) => setTenantSlug(event.target.value)}>
              {tenants.map((tenant) => (
                <option key={tenant.id} value={tenant.slug}>
                  {tenant.name}
                </option>
              ))}
            </select>

            <div className="hero-note">
              <span>{dashboard?.tenant?.name || 'Loading tenant...'}</span>
              <span>{dashboard ? `${formatNumber(dashboard.totals.records)} records loaded` : 'Waiting for data'}</span>
            </div>
          </div>
        </header>

        {error ? <div className="alert">{error}</div> : null}

        <section className="metric-grid">
          <article className="metric-card accent-blue">
            <span>Imported rows</span>
            <strong>{dashboard ? formatNumber(dashboard.totals.records) : '—'}</strong>
            <small>Seeded from 2 tenants and 3 source types</small>
          </article>
          <article className="metric-card accent-amber">
            <span>Pending review</span>
            <strong>{dashboard ? formatNumber(dashboard.totals.pending) : '—'}</strong>
            <small>Rows that need an analyst decision</small>
          </article>
          <article className="metric-card accent-red">
            <span>Suspicious rows</span>
            <strong>{dashboard ? formatNumber(dashboard.totals.flagged) : '—'}</strong>
            <small>Outliers, missing fields, or derived values</small>
          </article>
          <article className="metric-card accent-green">
            <span>Total CO2e</span>
            <strong>{dashboard ? formatNumber(dashboard.totals.co2e_kg, { maximumFractionDigits: 0 }) : '—'}</strong>
            <small>Aggregated normalized emissions in kgCO2e</small>
          </article>
        </section>

        <section className="content-grid">
          <div className="stack">
            <section className="panel">
              <div className="panel-head">
                <div>
                  <h2>Queue</h2>
                  <p>Prioritized by suspicious records first, then pending rows.</p>
                </div>

                <div className="filters">
                  <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                    <option value="all">All statuses</option>
                    {Object.entries(statusLabels).map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                  <select value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)}>
                    <option value="all">All sources</option>
                    {Object.entries(sourceLabels).map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                  <input
                    type="search"
                    placeholder="Search category, vendor, plant, airport..."
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                  />
                </div>
              </div>

              <div className="queue-list">
                {loading ? <div className="empty-state">Loading records...</div> : null}
                {!loading && records.length === 0 ? <div className="empty-state">No records match the current filter.</div> : null}
                {records.map((record) => (
                  <button
                    type="button"
                    key={record.id}
                    className={`queue-card ${selectedRecord?.id === record.id ? 'selected' : ''}`}
                    onClick={() => setSelectedId(record.id)}
                  >
                    <div className="queue-card-top">
                      <div>
                        <div className="queue-title">
                          <strong>{record.activity_label}</strong>
                          <span className={badgeClass(record.review_status)}>{statusLabels[record.review_status] || record.review_status}</span>
                        </div>
                        <p>{sourceLabels[record.source_type] || record.source_type} · Scope {record.scope} · {record.counterparty || record.location_code || 'No counterparty'}</p>
                      </div>
                      <div className="queue-value">
                        <strong>{formatNumber(record.co2e_kg)}</strong>
                        <span>kgCO2e</span>
                      </div>
                    </div>

                    <div className="queue-card-meta">
                      <span>{record.normalized_quantity} {record.normalized_unit}</span>
                      <span>Raw: {record.quantity} {record.original_unit}</span>
                      <span>{formatDate(record.activity_date)}</span>
                    </div>

                    {record.suspicious_reason ? <p className="warning-text">{record.suspicious_reason}</p> : null}
                  </button>
                ))}
              </div>
            </section>

            <section className="panel">
              <div className="panel-head compact">
                <div>
                  <h2>Source mix</h2>
                  <p>What came in from each intake channel.</p>
                </div>
              </div>

              <div className="source-grid">
                {(dashboard?.source_breakdown || []).map((source) => (
                  <article key={source.source_type} className="source-card">
                    <span>{sourceLabels[source.source_type] || source.source_type}</span>
                    <strong>{formatNumber(source.count)}</strong>
                    <small>{formatNumber(source.co2e_kg, { maximumFractionDigits: 0 })} kgCO2e</small>
                  </article>
                ))}
              </div>
            </section>
          </div>

          <aside className="panel detail-panel">
            {selectedRecord ? (
              <>
                <div className="panel-head compact">
                  <div>
                    <h2>Record detail</h2>
                    <p>{selectedRecord.source_system} · {selectedRecord.source_filename}</p>
                  </div>
                </div>

                <div className="detail-stack">
                  <div className="detail-hero">
                    <span className={badgeClass(selectedRecord.review_status)}>{statusLabels[selectedRecord.review_status] || selectedRecord.review_status}</span>
                    <h3>{selectedRecord.activity_label}</h3>
                    <p>{selectedRecord.suspicious_reason || 'No anomaly flagged for this row.'}</p>
                  </div>

                  <dl className="detail-grid">
                    <div>
                      <dt>Source of truth</dt>
                      <dd>{selectedRecord.source_reference}</dd>
                    </div>
                    <div>
                      <dt>Source row</dt>
                      <dd>{selectedRecord.external_id}</dd>
                    </div>
                    <div>
                      <dt>Period</dt>
                      <dd>{formatDate(selectedRecord.period_start)} to {formatDate(selectedRecord.period_end)}</dd>
                    </div>
                    <div>
                      <dt>Edited</dt>
                      <dd>{selectedRecord.edited_at ? `${formatDate(selectedRecord.edited_at)} by ${selectedRecord.edited_by_name || 'Analyst'}` : 'Not yet edited'}</dd>
                    </div>
                  </dl>

                  <div className="raw-block">
                    <div className="raw-block-head">
                      <span>Raw payload</span>
                      <span>{selectedRecord.raw_record}</span>
                    </div>
                    <pre>{JSON.stringify(selectedRecord.raw_payload, null, 2)}</pre>
                  </div>

                  <div className="action-row">
                    <button type="button" className="primary" disabled={savingId === selectedRecord.id} onClick={() => updateRecord(selectedRecord.id, 'approved')}>
                      Approve
                    </button>
                    <button type="button" className="secondary" disabled={savingId === selectedRecord.id} onClick={() => updateRecord(selectedRecord.id, 'flagged')}>
                      Flag
                    </button>
                    <button type="button" className="ghost" disabled={savingId === selectedRecord.id} onClick={() => updateRecord(selectedRecord.id, 'rejected')}>
                      Reject
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="empty-state">Select a row to inspect its source payload and review metadata.</div>
            )}
          </aside>
        </section>
      </main>
    </div>
  )
}