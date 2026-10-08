import type { Metric, Season } from './types';

export interface Headline {
  intro?: string;
  rows: { label: string; text: string }[];
}

export const percent = (s: Season): string => `${s.gapPercent.toFixed(2)}%`;

// The one points formatter: exactly 1 is singular (1 pt), everything else plural (0.5 pts, 290 pts).
export const points = (n: number): string => `${n} ${n === 1 ? 'pt' : 'pts'}`;

// Championship points as integer hundredths. The dataset carries at most two decimal places
// (pinned by a pipeline test), so extremes and ties can be compared exactly in integers
// rather than on rounded percentages or floating-point differences.
const hundredths = (n: number): number => Math.round(n * 100);
const gap = (s: Season): number => hundredths(s.champion.points) - hundredths(s.runnerUp.points);

// What each metric ranks by and how the headline words it. `compare` is positive when a's
// value is larger than b's and 0 only when the two are exactly equal.
const METRICS = {
  percent: {
    // gap(a)/champion(a) vs gap(b)/champion(b), cross-multiplied to stay in integers.
    compare: (a: Season, b: Season): number =>
      gap(a) * hundredths(b.champion.points) - gap(b) * hundredths(a.champion.points),
    measure: 'percentage title margin',
    largest: 'Most dominant:',
    smallest: 'Closest:',
    single: 'title margin',
    value: percent,
  },
  points: {
    compare: (a: Season, b: Season): number => gap(a) - gap(b),
    measure: 'championship points gap',
    largest: 'Largest points gap:',
    smallest: 'Smallest points gap:',
    single: 'points gap',
    value: (s: Season): string => points(s.gapPoints),
  },
} as const;

type Compare = (a: Season, b: Season) => number;

// The extreme by the metric's exact comparison, plus the years of every other season exactly
// tied with it, ascending. A tie keeps the earliest season as the extreme.
function pick(seasons: readonly Season[], compare: Compare, direction: 1 | -1): { season: Season; tied: number[] } {
  const season = seasons.reduce((best, s) => {
    const c = compare(s, best) * direction;
    return c > 0 || (c === 0 && s.year < best.year) ? s : best;
  });
  const tied = seasons
    .filter((s) => s !== season && compare(s, season) === 0)
    .map((s) => s.year)
    .sort((a, b) => a - b);
  return { season, tied };
}

// Headline for the seasons currently shown, ranked by the active metric.
export function headline(seasons: readonly Season[], metric: Metric): Headline | undefined {
  const [first] = seasons;
  if (first === undefined) return undefined;
  const m = METRICS[metric];
  const row = (direction: 1 | -1): string => {
    const { season: s, tied } = pick(seasons, m.compare, direction);
    const ties = tied.length > 0 ? ` (tied with ${tied.join(', ')})` : '';
    return `${s.champion.name}, ${s.year}${ties} — ${m.value(s)} over ${s.runnerUp.name}`;
  };
  if (seasons.length === 1) {
    return {
      rows: [
        {
          label: `${first.year} ${m.single}:`,
          text: `${first.champion.name} — ${m.value(first)} over ${first.runnerUp.name}.`,
        },
      ],
    };
  }
  const years = seasons.map((s) => s.year);
  return {
    intro: `Across ${seasons.length} championships (${Math.min(...years)}–${Math.max(...years)}), by ${m.measure} over the runner-up:`,
    rows: [
      { label: m.largest, text: row(1) },
      { label: m.smallest, text: row(-1) },
    ],
  };
}

// Arithmetic mean of the percentage margins.
export function meanPercent(seasons: readonly Season[]): number {
  return seasons.reduce((sum, s) => sum + s.gapPercent, 0) / seasons.length;
}

// Years whose champion is a less-frequent champion within a consecutive run of titles won by
// the same constructor: the run's top scorer, or tied top scorers, are not included. Give it
// the full dataset so a season's answer never depends on the selected range.
export function lessFrequentChampionYears(seasons: readonly Season[]): Set<number> {
  const striped = new Set<number>();
  const flush = (run: Season[]): void => {
    const titles = new Map<string, number>();
    for (const s of run) titles.set(s.champion.driverId, (titles.get(s.champion.driverId) ?? 0) + 1);
    const most = Math.max(...titles.values());
    for (const s of run) if ((titles.get(s.champion.driverId) ?? 0) < most) striped.add(s.year);
  };
  let run: Season[] = [];
  for (const s of [...seasons].sort((a, b) => a.year - b.year)) {
    const last = run[run.length - 1];
    if (last !== undefined && (last.champion.teamId !== s.champion.teamId || last.year + 1 !== s.year)) {
      flush(run);
      run = [];
    }
    run.push(s);
  }
  if (run.length > 0) flush(run);
  return striped;
}
