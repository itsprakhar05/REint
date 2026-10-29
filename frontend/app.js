const defaultStart = '2026-01-01T00:00:00Z';
const defaultEnd = '2026-01-02T00:00:00Z';

const state = {
  start: defaultStart,
  end: defaultEnd,
  result: null,
  series: [],
  error: '',
  loading: false,
};

const root = document.getElementById('app');

function buildLinePath(points) {
  if (!points.length) return '';
  return points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ');
}

function renderChart(series) {
  const chartHost = document.getElementById('chart');
  if (!chartHost) return;
  if (!series.length) {
    chartHost.innerHTML = '<div class="empty-chart">No series data available for this window.</div>';
    return;
  }

  const width = 720;
  const height = 260;
  const padding = 28;
  const values = series.flatMap((row) => [row.forecast_mw, row.actual_mw]);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const points = series.map((row, index) => {
    const x = padding + (index / Math.max(series.length - 1, 1)) * (width - padding * 2);
    const yForecast = height - padding - ((row.forecast_mw - min) / range) * (height - padding * 2);
    const yActual = height - padding - ((row.actual_mw - min) / range) * (height - padding * 2);
    return { x, forecastY: yForecast, actualY: yActual };
  });

  const forecastPath = buildLinePath(points.map((point) => ({ x: point.x, y: point.forecastY })));
  const actualPath = buildLinePath(points.map((point) => ({ x: point.x, y: point.actualY })));

  chartHost.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Forecast vs actual generation chart">
      <g>
        <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" stroke="rgba(148,163,184,0.5)" />
        <line x1="${padding}" y1="${padding}" x2="${padding}" y2="${height - padding}" stroke="rgba(148,163,184,0.5)" />
      </g>
      <path d="${actualPath}" fill="none" stroke="#60a5fa" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
      <path d="${forecastPath}" fill="none" stroke="#34d399" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
      <g>
        <text x="${padding}" y="${height - 8}" fill="#bfdbfe" font-size="10">${series[0].time.slice(11, 16)}</text>
        <text x="${width - padding - 32}" y="${height - 8}" fill="#bfdbfe" font-size="10">${series.at(-1).time.slice(11, 16)}</text>
      </g>
    </svg>
    <div class="chart-legend">
      <span><i class="legend-dot forecast"></i>Forecast</span>
      <span><i class="legend-dot actual"></i>Actual</span>
    </div>
  `;
}

function render() {
  root.innerHTML = `
    <header>
      <p class="eyebrow">REint</p>
      <h1>Wind Forecast Accuracy Dashboard</h1>
    </header>

    <main class="panel">
      <section class="controls">
        <div class="field">
          <label for="start">Start date</label>
          <input id="start" type="datetime-local" value="${state.start.slice(0, 16)}" />
        </div>

        <div class="field">
          <label for="end">End date</label>
          <input id="end" type="datetime-local" value="${state.end.slice(0, 16)}" />
        </div>

        <button id="submit" type="button" ${state.loading ? 'disabled' : ''}>
          ${state.loading ? 'Loading...' : 'Check forecast accuracy'}
        </button>
      </section>

      ${state.error ? `<div class="error">${state.error}</div>` : ''}

      ${state.result ? `
        <section class="metrics">
          <article class="metric accent">
            <span>Matched intervals</span>
            <strong>${state.result.matched_intervals}</strong>
          </article>
          <article class="metric">
            <span>MAE</span>
            <strong>${Number(state.result.mae_mw).toFixed(2)} MW</strong>
          </article>
          <article class="metric">
            <span>RMSE</span>
            <strong>${Number(state.result.rmse_mw).toFixed(2)} MW</strong>
          </article>
          <article class="metric">
            <span>Bias</span>
            <strong>${Number(state.result.bias_mw).toFixed(2)} MW</strong>
          </article>
        </section>
      ` : ''}

      <section class="chart-panel">
        <h2>Forecast vs Actual</h2>
        <div id="chart"></div>
      </section>
    </main>
  `;

  renderChart(state.series);

  document.getElementById('start').addEventListener('change', (event) => {
    state.start = `${event.target.value}:00Z`;
  });

  document.getElementById('end').addEventListener('change', (event) => {
    state.end = `${event.target.value}:00Z`;
  });

  document.getElementById('submit').addEventListener('click', async () => {
    state.loading = true;
    state.error = '';
    render();

    try {
      const params = new URLSearchParams({ start: state.start, end: state.end });
      const accuracyResponse = await fetch(`http://127.0.0.1:8000/api/v1/analytics/accuracy?${params.toString()}`);
      if (!accuracyResponse.ok) {
        const body = await accuracyResponse.json().catch(() => ({}));
        throw new Error(body.detail || 'Failed to fetch data');
      }
      state.result = await accuracyResponse.json();

      const seriesResponse = await fetch(`http://127.0.0.1:8000/api/v1/analytics/series?${params.toString()}`);
      if (!seriesResponse.ok) {
        const body = await seriesResponse.json().catch(() => ({}));
        throw new Error(body.detail || 'Failed to fetch chart data');
      }
      const seriesPayload = await seriesResponse.json();
      state.series = seriesPayload.series || [];
      renderChart(state.series);
    } catch (error) {
      state.result = null;
      state.series = [];
      state.error = error.message || 'Something went wrong';
      renderChart([]);
    } finally {
      state.loading = false;
      render();
    }
  });
}

async function loadInitialData() {
  const params = new URLSearchParams({ start: state.start, end: state.end });
  try {
    const [accuracyResponse, seriesResponse] = await Promise.all([
      fetch(`http://127.0.0.1:8000/api/v1/analytics/accuracy?${params.toString()}`),
      fetch(`http://127.0.0.1:8000/api/v1/analytics/series?${params.toString()}`),
    ]);

    if (accuracyResponse.ok) state.result = await accuracyResponse.json();
    if (seriesResponse.ok) {
      const seriesPayload = await seriesResponse.json();
      state.series = seriesPayload.series || [];
    }
  } catch (error) {
    state.error = 'Could not load initial chart data';
  }
  render();
}

loadInitialData();
