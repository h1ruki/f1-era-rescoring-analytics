import { describe, expect, it } from 'vitest'
import type { Data, ScatterData } from 'plotly.js'
import { chartSpec } from './chartModel'
import { seasons } from '../tests/fixtures'

function scatter(trace: Data): Partial<ScatterData> {
  expect(trace.type).toBe('scatter')
  return trace as Partial<ScatterData>
}

describe('chronological lollipop geometry', () => {
  it('creates independent stems and a markers-only trace in chronological order', () => {
    const { traces, layout } = chartSpec([...seasons].reverse(), 'percentage')
    expect(traces).toHaveLength(5)
    for (const [index, trace] of traces.slice(0, 4).entries()) {
      const stem = scatter(trace)
      expect(stem.mode).toBe('lines')
      expect(stem.x).toEqual([0, seasons[index].margin.championship_margin_percent.plot])
      expect(stem.y).toEqual([String(seasons[index].season), String(seasons[index].season)])
    }
    expect(scatter(traces[4]).mode).toBe('markers')
    expect(scatter(traces[4]).x).toEqual(seasons.map(row => row.margin.championship_margin_percent.plot))
    expect(layout.yaxis?.categoryarray).toEqual(['2010', '2011', '2012', '2013'])
  })

  it('uses backend plot values even when they differ from P1/P2 arithmetic', () => {
    const row = structuredClone(seasons[0])
    row.margin.championship_margin_percent.plot = 67.89
    row.margin.raw_points_gap.plot = 42
    const percent = chartSpec([row], 'percentage')
    const points = chartSpec([row], 'points')
    expect(scatter(percent.traces[0]).x).toEqual([0, 67.89])
    expect(scatter(points.traces[0]).x).toEqual([0, 42])
    expect(points.layout.xaxis?.title).toEqual({ text: 'Points Gap' })
  })
})
