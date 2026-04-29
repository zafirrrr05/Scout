import { useState, useEffect } from 'react'
import { fetchEvals } from '../api.js'

const DIMS = [
  { key: 'anticipatory_accuracy', label: 'Anticipatory' },
  { key: 'unknown_unknown_quality', label: 'Unknown UNK' },
  { key: 'safety_conservatism', label: 'Safety' },
  { key: 'arabic_naturalness', label: 'Arabic' },
  { key: 'groundedness', label: 'Grounded' },
]

function scoreClass(score) {
  if (score >= 4) return 'high'
  if (score >= 3) return 'mid'
  return 'low'
}

export default function EvalDashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchEvals()
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="eval-view">
        <div className="eval-no-data">
          <div style={{ fontSize: 32 }}>⏳</div>
          <h3>Loading eval results...</h3>
        </div>
      </div>
    )
  }

  if (!data || !data.cases || data.cases.length === 0) {
    return (
      <div className="eval-view">
        <div className="eval-header">
          <h2>Eval Dashboard</h2>
          <p>Judge-LLM scored results across 16 test cases</p>
        </div>
        <div className="eval-no-data" style={{ background: 'white', borderRadius: 20, padding: 48 }}>
          <div style={{ fontSize: 40 }}>📊</div>
          <h3>Evals not yet run</h3>
          <p style={{ marginTop: 8, marginBottom: 16 }}>
            Start the backend, then run the eval harness:
          </p>
          <code>python -m evals.judge</code>
          <p style={{ marginTop: 16, fontSize: 13, color: 'var(--ink-muted)' }}>
            Results will appear here automatically once complete.
          </p>
        </div>
      </div>
    )
  }

  const cases = data.cases || []
  const passed = cases.filter(c => c.passed).length
  const passRate = cases.length > 0 ? Math.round((passed / cases.length) * 100) : 0

  const dimAverages = DIMS.map(dim => {
    const scores = cases
      .filter(c => c.scores && c.scores[dim.key] != null)
      .map(c => c.scores[dim.key])
    const avg = scores.length > 0 ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : '—'
    return { ...dim, avg }
  })

  const overallAvg = cases
    .filter(c => c.aggregate)
    .map(c => c.aggregate)
  const avgScore = overallAvg.length > 0
    ? (overallAvg.reduce((a, b) => a + b, 0) / overallAvg.length).toFixed(2)
    : '—'

  return (
    <div className="eval-view">
      <div className="eval-header">
        <h2>Eval Dashboard</h2>
        <p>Judge-LLM (GPT-4o-mini) scored across {cases.length} test cases · {data.run_at || 'see EVALS.md'}</p>
      </div>

      <div className="eval-summary-row">
        <div className="eval-stat-card">
          <div className="eval-stat-label">Pass Rate</div>
          <div className="eval-stat-value" style={{ color: passRate >= 70 ? 'var(--sage)' : 'var(--terracotta)' }}>
            {passRate}%
          </div>
        </div>
        <div className="eval-stat-card">
          <div className="eval-stat-label">Passed / Total</div>
          <div className="eval-stat-value">{passed}/{cases.length}</div>
        </div>
        <div className="eval-stat-card">
          <div className="eval-stat-label">Avg Score</div>
          <div className="eval-stat-value">{avgScore}<span style={{ fontSize: 16, color: 'var(--ink-muted)' }}>/5</span></div>
        </div>
        {dimAverages.map(d => (
          <div key={d.key} className="eval-stat-card">
            <div className="eval-stat-label">{d.label}</div>
            <div className="eval-stat-value" style={{ fontSize: 22 }}>{d.avg}</div>
          </div>
        ))}
      </div>

      <div className="eval-table-wrap">
        <table className="eval-table">
          <thead>
            <tr>
              <th>Case</th>
              <th>Category</th>
              {DIMS.map(d => <th key={d.key}>{d.label}</th>)}
              <th>Avg</th>
              <th>Pass</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            {cases.map(c => (
              <tr key={c.case_id}>
                <td style={{ fontWeight: 600, fontSize: 12 }}>{c.case_id}</td>
                <td style={{ fontSize: 11, color: 'var(--ink-muted)' }}>{c.category}</td>
                {DIMS.map(d => {
                  const s = c.scores?.[d.key]
                  return (
                    <td key={d.key}>
                      {s != null
                        ? <span className={`score-chip ${scoreClass(s)}`}>{s}</span>
                        : <span style={{ color: 'var(--ink-muted)', fontSize: 11 }}>—</span>
                      }
                    </td>
                  )
                })}
                <td style={{ fontWeight: 600 }}>{c.aggregate?.toFixed(1) || '—'}</td>
                <td className="pass-icon">{c.passed ? '✅' : '❌'}</td>
                <td style={{ fontSize: 11, color: 'var(--ink-muted)', maxWidth: 160 }}>{(c.notes || '').slice(0, 60)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ fontSize: 13, color: 'var(--ink-muted)', lineHeight: 1.6 }}>
        <strong>Known failure modes:</strong> Sparse inputs correctly trigger clarification (counted as pass) ·
        Medical queries refused conservatively · Arabic naturalness depends on OpenRouter availability ·
        Graph coverage gaps degrade gracefully with explanation.
      </div>
    </div>
  )
}
