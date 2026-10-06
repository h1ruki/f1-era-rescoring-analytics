import { afterEach, describe, expect, it, vi } from 'vitest'
import { getChampionshipMargins } from './client'
import { response } from '../tests/fixtures'

afterEach(() => vi.restoreAllMocks())

describe('championship margins API client', () => {
  it('consumes the backend Original Drivers response without changing values', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true, json: async () => response,
    } as Response)
    const result = await getChampionshipMargins()
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/championship-margins?category=drivers&scoring=original',
      { signal: undefined },
    )
    expect(result).toEqual(response)
    expect(result.results[2].availability).toBe('available')
    if (result.results[2].availability === 'available') {
      expect(result.results[2].margin.championship_margin_percent.exact)
        .toEqual({ numerator: 300, denominator: 281 })
    }
  })

  it('rejects HTTP errors and malformed responses', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({ ok: false, status: 503 } as Response)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ results: [] }) } as Response)
    await expect(getChampionshipMargins()).rejects.toThrow('API request failed (503)')
    await expect(getChampionshipMargins()).rejects.toThrow('invalid championship margins response')
  })
})
