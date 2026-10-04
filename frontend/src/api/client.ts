import type { MarginsResponse } from './types'

const MARGINS_URL = '/api/v1/championship-margins?category=drivers&scoring=original'

export async function getChampionshipMargins(signal?: AbortSignal): Promise<MarginsResponse> {
  const response = await fetch(MARGINS_URL, { signal })
  if (!response.ok) {
    throw new Error(`API request failed (${response.status})`)
  }
  const payload: unknown = await response.json()
  if (!isMarginsResponse(payload)) {
    throw new Error('API returned an invalid championship margins response')
  }
  return payload
}

function isProjectedValue(value: unknown): boolean {
  if (typeof value !== 'object' || value === null) return false
  const item = value as Record<string, unknown>
  const exact = item.exact as Record<string, unknown> | null
  return typeof item.plot === 'number' && Number.isFinite(item.plot)
    && typeof exact?.numerator === 'number' && typeof exact?.denominator === 'number'
    && exact.denominator > 0
}

function isMarginsResponse(value: unknown): value is MarginsResponse {
  if (typeof value !== 'object' || value === null) return false
  const body = value as Record<string, unknown>
  if (body.category !== 'drivers' || body.scoring !== 'original' || !Array.isArray(body.results)) {
    return false
  }
  return body.results.every((entry: unknown) => {
    if (typeof entry !== 'object' || entry === null) return false
    const item = entry as Record<string, unknown>
    if (!Number.isInteger(item.season) || item.category !== 'drivers') return false
    if (item.availability === 'unavailable') {
      return typeof item.reason === 'string' && item.margin === null
    }
    if (item.availability !== 'available') return false
    const champion = item.champion as Record<string, unknown> | null
    const runnerUp = item.runner_up as Record<string, unknown> | null
    const margin = item.margin as Record<string, unknown> | null
    return typeof champion?.id === 'string' && typeof runnerUp?.id === 'string'
      && isProjectedValue(champion.points) && isProjectedValue(runnerUp.points)
      && isProjectedValue(margin?.raw_points_gap)
      && isProjectedValue(margin?.championship_margin_percent)
  })
}
