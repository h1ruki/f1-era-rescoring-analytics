import type { AvailableSeason, MarginsResponse, UnavailableSeason } from '../api/types'

const values = [
  { season: 2010, p1: 256, p2: 252, gap: 4, numerator: 25, denominator: 16, plot: 1.5625, champion: 'Sebastian Vettel', runner: 'Fernando Alonso' },
  { season: 2011, p1: 392, p2: 270, gap: 122, numerator: 1525, denominator: 49, plot: 31.122448979591837, champion: 'Sebastian Vettel', runner: 'Jenson Button' },
  { season: 2012, p1: 281, p2: 278, gap: 3, numerator: 300, denominator: 281, plot: 1.0676156583629892, champion: 'Sebastian Vettel', runner: 'Fernando Alonso' },
  { season: 2013, p1: 397, p2: 242, gap: 155, numerator: 15500, denominator: 397, plot: 39.042821158690176, champion: 'Sebastian Vettel', runner: 'Fernando Alonso' },
]

export const seasons: AvailableSeason[] = values.map(item => ({
  season: item.season,
  category: 'drivers',
  scoring: 'original',
  package: `original-${item.season}`,
  calculation_version: 'original-drivers-2010-2013-v1',
  availability: 'available',
  champion: {
    id: 'sebastian-vettel', name: item.champion, position: 1,
    points: { exact: { numerator: item.p1, denominator: 1 }, plot: item.p1 },
    constructor_contributions: [],
  },
  runner_up: {
    id: item.runner.toLowerCase().replace(' ', '-'), name: item.runner, position: 2,
    points: { exact: { numerator: item.p2, denominator: 1 }, plot: item.p2 },
    constructor_contributions: [],
  },
  margin: {
    raw_points_gap: { exact: { numerator: item.gap, denominator: 1 }, plot: item.gap },
    championship_margin_percent: {
      exact: { numerator: item.numerator, denominator: item.denominator }, plot: item.plot,
    },
  },
  reconciliation: {
    event_awards_match: true,
    recorded_driver_standings_match: true,
    event_award_difference_count: 0,
    standing_difference_count: 0,
  },
}))

export const response: MarginsResponse = {
  category: 'drivers', scoring: 'original', results: seasons,
}

export const unavailable: UnavailableSeason = {
  season: 2014, category: 'drivers', scoring: 'original', package: null,
  calculation_version: null, availability: 'unavailable',
  reason: 'Original source-year package is unsupported',
  resolution: 'Add a sourced and verified package for this year',
  champion: null, runner_up: null, margin: null, reconciliation: null,
}
