import { useEffect, useRef } from 'react'
import Plotly from 'plotly.js/lib/core'
import scatter from 'plotly.js/lib/scatter'
import type { AvailableSeason, Metric } from '../api/types'
import { chartSpec } from './chartModel'

Plotly.register(scatter)

type Props = {
  seasons: AvailableSeason[]
  metric: Metric
}

export default function ChampionshipMarginChart({ seasons, metric }: Props) {
  const plotRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const element = plotRef.current
    if (!element) return
    const { traces, layout } = chartSpec(seasons, metric)
    void Plotly.newPlot(element, traces, layout, {
      displayModeBar: false,
      responsive: true,
    })
    return () => { Plotly.purge(element) }
  }, [seasons, metric])

  return <div ref={plotRef} className="chart" role="img"
    aria-label={`Chronological lollipop chart of ${metric === 'percentage' ? 'Championship Margin percentages' : 'Points Gaps'}`} />
}
