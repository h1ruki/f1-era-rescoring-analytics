import type { Data, Layout } from 'plotly.js'
import type { AvailableSeason, Metric } from '../api/types'

export function chronological(rows: AvailableSeason[]): AvailableSeason[] {
  return [...rows].sort((a, b) => a.season - b.season)
}

export function metricValue(row: AvailableSeason, metric: Metric): number {
  return metric === 'percentage'
    ? row.margin.championship_margin_percent.plot
    : row.margin.raw_points_gap.plot
}

export function metricLabel(metric: Metric): string {
  return metric === 'percentage' ? 'Championship Margin (%)' : 'Points Gap'
}

function exactText(numerator: number, denominator: number): string {
  return denominator === 1 ? String(numerator) : `${numerator}/${denominator}`
}

function escapeHover(text: string): string {
  return text.replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[character]!)
}

export function chartSpec(rows: AvailableSeason[], metric: Metric): {
  traces: Data[]
  layout: Partial<Layout>
} {
  const ordered = chronological(rows)
  const seasons = ordered.map(row => String(row.season))
  const stems: Data[] = ordered.map(row => ({
    type: 'scatter',
    mode: 'lines',
    x: [0, metricValue(row, metric)],
    y: [String(row.season), String(row.season)],
    line: { color: '#5a7088', width: 3 },
    hoverinfo: 'skip',
    showlegend: false,
  }))
  const dots: Data = {
    type: 'scatter',
    mode: 'markers',
    x: ordered.map(row => metricValue(row, metric)),
    y: seasons,
    marker: { color: '#dbe8f3', size: 13, line: { color: '#8fb7d1', width: 2 } },
    text: ordered.map(row => {
      const winner = escapeHover(row.champion.name ?? row.champion.id)
      const second = escapeHover(row.runner_up.name ?? row.runner_up.id)
      const p1 = row.champion.points.exact
      const p2 = row.runner_up.points.exact
      return `${row.season} · ${winner} over ${second}<br>`
        + `P1 ${exactText(p1.numerator, p1.denominator)} · P2 ${exactText(p2.numerator, p2.denominator)}`
    }),
    hovertemplate: `%{text}<br>${metricLabel(metric)}: %{x:.2f}${metric === 'percentage' ? '%' : ' pts'}<extra></extra>`,
    showlegend: false,
  }
  return {
    traces: [...stems, dots],
    layout: {
      paper_bgcolor: '#101c2b',
      plot_bgcolor: '#101c2b',
      font: { color: '#dbe8f3', family: 'Inter, Segoe UI, sans-serif', size: 13 },
      margin: { l: 62, r: 28, t: 16, b: 65 },
      xaxis: {
        title: { text: metricLabel(metric) },
        rangemode: 'tozero',
        zeroline: true,
        zerolinecolor: '#8092a7',
        gridcolor: '#26374c',
        ticksuffix: metric === 'percentage' ? '%' : '',
      },
      yaxis: {
        type: 'category',
        categoryorder: 'array',
        categoryarray: seasons,
        autorange: 'reversed',
        title: { text: 'Season' },
      },
      showlegend: false,
      hovermode: 'closest',
      height: 410,
    },
  }
}
