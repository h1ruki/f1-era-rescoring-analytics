import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import Plotly from 'plotly.js/lib/core'
import type { Data, Layout, ScatterData } from 'plotly.js'
import App from './App'
import { response, seasons, unavailable } from './tests/fixtures'

vi.mock('plotly.js/lib/core', () => ({
  default: { register: vi.fn(), newPlot: vi.fn().mockResolvedValue(undefined), purge: vi.fn() },
}))
vi.mock('plotly.js/lib/scatter', () => ({ default: {} }))

function lastPlot(): { traces: Data[]; layout: Partial<Layout> } {
  const [, traces, layout] = vi.mocked(Plotly.newPlot).mock.calls.at(-1)! as unknown as
    [HTMLElement, Data[], Partial<Layout>]
  return { traces, layout }
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

describe('first visual slice', () => {
  it('shows loading, then four chronological API-driven seasons with percentage default', async () => {
    let resolveFetch!: (value: Response) => void
    vi.spyOn(globalThis, 'fetch').mockReturnValue(new Promise(resolve => { resolveFetch = resolve }))
    render(<App />)
    expect(screen.getByRole('status').textContent).toContain('Loading championship results')
    resolveFetch({ ok: true, json: async () => response } as Response)
    await screen.findByText('1.56%')
    expect(screen.getByRole('button', { name: 'Championship Margin (%)' }).getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByRole('button', { name: 'Points Gap' }).getAttribute('aria-pressed')).toBe('false')
    const observations = screen.getByRole('list', { name: 'Season observations' })
    expect(observations.textContent).toMatch(/2010.*2011.*2012.*2013/)
    expect(observations.textContent).toContain('31.12%')
    expect(observations.textContent).toContain('1.07%')
    expect(observations.textContent).toContain('39.04%')
    expect(screen.getByRole('img').getAttribute('aria-label')).toContain('Championship Margin')
    expect(screen.getByText(/Curated PoC coverage/)).toBeTruthy()
    expect(screen.getByRole('button', { name: /Constructors/ }).hasAttribute('disabled')).toBe(true)
    expect(screen.getByRole('button', { name: 'Drivers' }).getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByRole('button', { name: 'Drivers' }).hasAttribute('disabled')).toBe(false)
    expect(screen.getByText('Original')).toBeTruthy()
    await waitFor(() => expect(Plotly.newPlot).toHaveBeenCalled())
    const { traces, layout } = lastPlot()
    expect(traces).toHaveLength(5) // Four independent stems and one marker trace.
    expect((traces[4] as Partial<ScatterData>).x).toEqual(['2010', '2011', '2012', '2013'])
    expect((traces[4] as Partial<ScatterData>).y).toEqual(seasons.map(row => row.margin.championship_margin_percent.plot))
    expect(layout.xaxis?.categoryarray).toEqual(['2010', '2011', '2012', '2013'])
  })

  it('switches to the backend-provided raw gap plot values', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({ ok: true, json: async () => response } as Response)
    render(<App />)
    await screen.findByText('1.56%')
    fireEvent.click(screen.getByRole('button', { name: 'Points Gap' }))
    expect(screen.getByRole('button', { name: 'Points Gap' }).getAttribute('aria-pressed')).toBe('true')
    const observations = screen.getByRole('list', { name: 'Season observations' })
    expect(observations.textContent).toContain('4.00 pts')
    expect(observations.textContent).toContain('122.00 pts')
    expect(observations.textContent).toContain('3.00 pts')
    expect(observations.textContent).toContain('155.00 pts')
    expect(screen.getByRole('img').getAttribute('aria-label')).toContain('Points Gaps')
    await waitFor(() => {
      const { traces, layout } = lastPlot()
      expect((traces[4] as Partial<ScatterData>).y).toEqual(seasons.map(row => row.margin.raw_points_gap.plot))
      expect(layout.yaxis?.title).toEqual({ text: 'Points Gap' })
    })
  })

  it('reports API errors and allows retry', async () => {
    vi.spyOn(globalThis, 'fetch')
      .mockRejectedValueOnce(new Error('Network down'))
      .mockResolvedValueOnce({ ok: true, json: async () => response } as Response)
    render(<App />)
    expect((await screen.findByRole('alert')).textContent).toContain('Network down')
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
    await screen.findByText('1.56%')
  })

  it('renders explicit unavailable seasons and no fabricated chart when all are unavailable', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true, json: async () => ({ ...response, results: [unavailable] }),
    } as Response)
    render(<App />)
    await waitFor(() => expect(screen.getByText(/No supported championship results/)).toBeTruthy())
    expect(screen.getByText(/2014: Original source-year package is unsupported/)).toBeTruthy()
    expect(screen.queryByRole('img')).toBeNull()
  })
})
