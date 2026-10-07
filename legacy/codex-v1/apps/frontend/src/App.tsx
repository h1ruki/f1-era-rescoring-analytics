import { useEffect, useState } from 'react'
import { getChampionshipMargins } from './api/client'
import type { AvailableSeason, MarginsResponse, Metric, UnavailableSeason } from './api/types'
import ChampionshipMarginChart from './components/ChampionshipMarginChart'
import { chronological, metricLabel, metricValue } from './components/chartModel'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; data: MarginsResponse }

function displayValue(value: number, metric: Metric): string {
  const text = new Intl.NumberFormat('en-GB', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
  return metric === 'percentage' ? `${text}%` : `${text} pts`
}

export default function App() {
  const [metric, setMetric] = useState<Metric>('percentage')
  const [load, setLoad] = useState<LoadState>({ status: 'loading' })
  const [requestNumber, setRequestNumber] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    getChampionshipMargins(controller.signal).then(
      data => {
        if (!controller.signal.aborted) setLoad({ status: 'ready', data })
      },
      error => {
        if (!controller.signal.aborted) {
          setLoad({ status: 'error', message: error instanceof Error ? error.message : 'Unknown error' })
        }
      },
    )
    return () => controller.abort()
  }, [requestNumber])

  const available: AvailableSeason[] = load.status === 'ready'
    ? chronological(load.data.results.filter((row): row is AvailableSeason => row.availability === 'available'))
    : []
  const unavailable: UnavailableSeason[] = load.status === 'ready'
    ? load.data.results.filter((row): row is UnavailableSeason => row.availability === 'unavailable')
    : []

  return <main className="shell">
    <header className="page-header">
      <div className="eyebrow">Historical Formula 1 dominance analytics</div>
      <h1>F1 ERAs</h1>
      <p>How dominant was each F1 champion in their title-winning season?</p>
    </header>

    <section className="toolbar" aria-label="Chart controls">
      <div className="control-group">
        <span className="control-label">Metric</span>
        <div className="segmented" aria-label="Metric">
          <button type="button" aria-pressed={metric === 'percentage'}
            onClick={() => setMetric('percentage')}>Championship Margin (%)</button>
          <button type="button" aria-pressed={metric === 'points'}
            onClick={() => setMetric('points')}>Points Gap</button>
        </div>
      </div>
      <div className="control-group">
        <span className="control-label">Category</span>
        <div className="segmented" aria-label="Category">
          <button type="button" aria-pressed="true">Drivers</button>
          <button type="button" disabled title="Constructor championship calculation is not implemented">Constructors · unavailable</button>
        </div>
      </div>
      <div className="control-group">
        <span className="control-label">Scoring context</span>
        <span className="static-control">Original</span>
      </div>
    </section>

    <section className="panel" aria-label="Championship margin visualization">
      <div className="panel-head">
        <div>
          <div className="eyebrow">Curated PoC coverage · 2010–2013</div>
          <h2>{metricLabel(metric)}</h2>
        </div>
        <span className="legend"><span className="legend-dot" /> Each season stands alone</span>
      </div>
      {load.status === 'loading' && <div role="status" className="message">Loading championship results…</div>}
      {load.status === 'error' && <div role="alert" className="message">
        Could not load championship results: {load.message}
        <button type="button" className="retry" onClick={() => {
          setLoad({ status: 'loading' })
          setRequestNumber(value => value + 1)
        }}>Retry</button>
      </div>}
      {load.status === 'ready' && available.length === 0 &&
        <div role="status" className="message">No supported championship results are available.</div>}
      {load.status === 'ready' && available.length > 0 && <>
        <ChampionshipMarginChart seasons={available} metric={metric} />
        <ol className="season-list" aria-label="Season observations">
          {available.map(row => <li key={row.season}>
            <span className="season-year">{row.season}</span>
            <span className="season-driver">{row.champion.name ?? row.champion.id}</span>
            <strong>{displayValue(metricValue(row, metric), metric)}</strong>
          </li>)}
        </ol>
      </>}
      {unavailable.length > 0 && <div className="unavailable" role="status">
        <h3>Unavailable seasons</h3>
        {unavailable.map(row => <p key={row.season}>{row.season}: {row.reason}</p>)}
      </div>}
    </section>
    <footer>Original scoring · Drivers only · Reconstructed results are distinct from recorded standings.</footer>
  </main>
}
