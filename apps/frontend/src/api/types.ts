export type ExactFraction = {
  numerator: number
  denominator: number
}

export type ProjectedValue = {
  exact: ExactFraction
  plot: number
}

export type ConstructorContribution = {
  constructor_id: string
  constructor_name: string | null
  counted_points: ProjectedValue
}

export type DriverResult = {
  id: string
  name: string | null
  position: number
  points: ProjectedValue
  constructor_contributions: ConstructorContribution[]
}

export type Reconciliation = {
  event_awards_match: boolean
  recorded_driver_standings_match: boolean
  event_award_difference_count: number
  standing_difference_count: number
}

export type ChampionshipMargin = {
  raw_points_gap: ProjectedValue
  championship_margin_percent: ProjectedValue
}

type CommonSeason = {
  season: number
  category: 'drivers' | 'constructors'
  scoring: 'original'
  package: string | null
  calculation_version: string | null
}

export type AvailableSeason = CommonSeason & {
  availability: 'available'
  champion: DriverResult
  runner_up: DriverResult
  margin: ChampionshipMargin
  reconciliation: Reconciliation
}

export type UnavailableSeason = CommonSeason & {
  availability: 'unavailable'
  reason: string
  resolution: string
  champion: null
  runner_up: null
  margin: null
  reconciliation: null
}

export type SeasonResult = AvailableSeason | UnavailableSeason

export type MarginsResponse = {
  category: 'drivers' | 'constructors'
  scoring: 'original'
  results: SeasonResult[]
}

export type Metric = 'percentage' | 'points'
