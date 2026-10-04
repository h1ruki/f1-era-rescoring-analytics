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
      expect(stem.x).toEqual([String(seasons[index].season), String(seasons[index].season)])
      expect(stem.y).toEqual([0, seasons[index].margin.championship_margin_percent.plot])
    }
    expect(scatter(traces[4]).mode).toBe('markers')
    expect(scatter(traces[4]).x).toEqual(['2010', '2011', '2012', '2013'])
    expect(scatter(traces[4]).y).toEqual(seasons.map(row => row.margin.championship_margin_percent.plot))
    expect(layout.xaxis?.type).toBe('category')
    expect(layout.xaxis?.categoryorder).toBe('array')
    expect(layout.xaxis?.categoryarray).toEqual(['2010', '2011', '2012', '2013'])
    expect(layout.xaxis?.title).toEqual({ text: 'Season' })
    expect(layout.yaxis?.title).toEqual({ text: 'Championship Margin (%)' })
    expect(layout.yaxis?.rangemode).toBe('tozero')
    expect(scatter(traces[4]).hovertemplate).toContain('%{y:.2f}%')
  })

  it('uses backend plot values even when they differ from P1/P2 arithmetic', () => {
    const row = structuredClone(seasons[0])
    row.margin.championship_margin_percent.plot = 67.89
    row.margin.raw_points_gap.plot = 42
    const percent = chartSpec([row], 'percentage')
    const points = chartSpec([row], 'points')
    expect(scatter(percent.traces[0]).x).toEqual(['2010', '2010'])
    expect(scatter(percent.traces[0]).y).toEqual([0, 67.89])
    expect(scatter(points.traces[0]).x).toEqual(['2010', '2010'])
    expect(scatter(points.traces[0]).y).toEqual([0, 42])
    expect(scatter(percent.traces[1]).y).toEqual([67.89])
    expect(scatter(points.traces[1]).y).toEqual([42])
    expect(points.layout.yaxis?.title).toEqual({ text: 'Points Gap' })
    expect(scatter(points.traces[1]).hovertemplate).toContain('%{y:.2f} pts')
  })
})
