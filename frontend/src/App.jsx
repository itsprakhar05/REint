import { useEffect, useState } from 'react'
import './App.css'

const DEFAULT_START = '2026-01-01T00:00:00Z'
const DEFAULT_END = '2026-01-02T00:00:00Z'
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const buildLinePath = (points) => {
  if (!points.length) return ''
  return points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ')
}

const formatTimeLabel = (value) => {
  if (!value) return ''
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function App() {
  const [start, setStart] = useState(DEFAULT_START)
  const [end, setEnd] = useState(DEFAULT_END)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [series, setSeries] = useState([])
  const [error, setError] = useState('')

  const fetchDashboardData = async () => {
    setLoading(true)
    setError('')

    try {
      const params = new URLSearchParams({ start, end })
      const [accuracyResponse, seriesResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/api/v1/analytics/accuracy?${params.toString()}`),
        fetch(`${API_BASE_URL}/api/v1/analytics/series?${params.toString()}`),
      ])

      if (!accuracyResponse.ok) {
        const body = await accuracyResponse.json().catch(() => ({}))
        throw new Error(body.detail || 'Failed to fetch analytics data')
      }

      if (!seriesResponse.ok) {
        const body = await seriesResponse.json().catch(() => ({}))
        throw new Error(body.detail || 'Failed to fetch chart data')
      }

      const metrics = await accuracyResponse.json()
      const seriesPayload = await seriesResponse.json()
      setResult(metrics)
      setSeries(seriesPayload.series || [])
    } catch (err) {
      setError(err.message || 'Something went wrong')
      setResult(null)
      setSeries([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const chart = (() => {
    if (!series.length) return null

    const width = 720
    const height = 260
    const padding = 28
    const values = series.flatMap((entry) => [entry.forecast_mw, entry.actual_mw])
    const min = Math.min(...values)
    const max = Math.max(...values)
    const range = max - min || 1

    const points = series.map((entry, index) => {
      const x = padding + (index / Math.max(series.length - 1, 1)) * (width - padding * 2)
      const forecastY = height - padding - ((entry.forecast_mw - min) / range) * (height - padding * 2)
      const actualY = height - padding - ((entry.actual_mw - min) / range) * (height - padding * 2)
      return { x, forecastY, actualY }
    })

    const forecastPath = buildLinePath(points.map((point) => ({ x: point.x, y: point.forecastY })))
    const actualPath = buildLinePath(points.map((point) => ({ x: point.x, y: point.actualY })))

    return { width, height, padding, forecastPath, actualPath, points }
  })()

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">REint</p>
          <h1>Wind Forecast Accuracy Dashboard</h1>
        </div>
      </header>

      <main className="panel">
        <section className="controls">
          <div className="field-group">
            <label htmlFor="start">Start date</label>
            <input
              id="start"
              type="datetime-local"
              value={start.slice(0, 16)}
              onChange={(event) => {
                const value = event.target.value
                setStart(`${value}:00Z`)
              }}
            />
          </div>

          <div className="field-group">
            <label htmlFor="end">End date</label>
            <input
              id="end"
              type="datetime-local"
              value={end.slice(0, 16)}
              onChange={(event) => {
                const value = event.target.value
                setEnd(`${value}:00Z`)
              }}
            />
          </div>

          <button type="button" onClick={fetchDashboardData} disabled={loading}>
            {loading ? 'Loading...' : 'Check forecast accuracy'}
          </button>
        </section>

        {error && <div className="error-box">{error}</div>}

        {result && (
          <section className="metrics-grid">
            <article className="metric-card accent">
              <span>Matched intervals</span>
              <strong>{result.matched_intervals}</strong>
            </article>

            <article className="metric-card">
              <span>MAE</span>
              <strong>{Number(result.mae_mw).toFixed(2)} MW</strong>
            </article>

            <article className="metric-card">
              <span>RMSE</span>
              <strong>{Number(result.rmse_mw).toFixed(2)} MW</strong>
            </article>

            <article className="metric-card">
              <span>Bias</span>
              <strong>{Number(result.bias_mw).toFixed(2)} MW</strong>
            </article>
          </section>
        )}

        <section className="chart-card">
          <div className="chart-header">
            <h2>Forecast vs Actual</h2>
          </div>

          {chart ? (
            <>
              <svg viewBox={`0 0 ${chart.width} ${chart.height}`} className="chart-svg" role="img" aria-label="Forecast and actual wind generation over time">
                <g>
                  <line x1={chart.padding} y1={chart.height - chart.padding} x2={chart.width - chart.padding} y2={chart.height - chart.padding} stroke="rgba(148,163,184,0.5)" />
                  <line x1={chart.padding} y1={chart.padding} x2={chart.padding} y2={chart.height - chart.padding} stroke="rgba(148,163,184,0.5)" />
                </g>
                <path d={chart.actualPath} fill="none" stroke="#60a5fa" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                <path d={chart.forecastPath} fill="none" stroke="#34d399" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
                <g>
                  <text x={chart.padding} y={chart.height - 8} fill="#bfdbfe" fontSize="10">{formatTimeLabel(series[0].time)}</text>
                  <text x={chart.width - chart.padding - 32} y={chart.height - 8} fill="#bfdbfe" fontSize="10">{formatTimeLabel(series.at(-1).time)}</text>
                </g>
              </svg>

              <div className="chart-legend">
                <span><i className="legend-dot forecast-dot" />Forecast</span>
                <span><i className="legend-dot actual-dot" />Actual</span>
              </div>
            </>
          ) : (
            <div className="empty-chart">No series data available for this window.</div>
          )}
        </section>
      </main>
    </div>
  )
}

export default App
