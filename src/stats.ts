import type { Metric, Season } from './types';

export interface Headline {
  intro?: string;
  rows: { label: string; text: string }[];
}

export const percent = (s: Season): string => `${s.gapPercent.toFixed(2)}%`;

// The one points formatter: exactly 1 is singular (1 pt), everything else plural (0.5 pts, 290 pts).
export const points = (n: number): string => `${n} ${n === 1 ? 'pt' : 'pts'}`;

// What each metric ranks by and how the headline words it.
const METRICS = {
  percent: {
    key: 'gapPercent',
    measure: 'percentage title margin',
    largest: 'Most dominant:',
    smallest: 'Closest:',
    single: 'title margin',
    value: percent,
  },
  points: {
    key: 'gapPoints',
    measure: 'championship points gap',
    largest: 'Largest points gap:',
    smallest: 'Smallest points gap:',
    single: 'points gap',
    value: (s: Season): string => points(s.gapPoints),
  },
} as const;

// Extremes by the metric's value; a tie keeps the earlier season.
function pick(seasons: readonly Season[], key: 'gapPercent' | 'gapPoints', direction: 1 | -1): Season {
  return seasons.reduce((best, s) =>
    (s[key] - best[key]) * direction > 0 || (s[key] === best[key] && s.year < best.year) ? s : best,
  );
}

// Headline for the seasons currently shown, ranked by the active metric.
export function headline(seasons: readonly Season[], metric: Metric): Headline | undefined {
  const [first] = seasons;
  if (first === undefined) return undefined;
  const m = METRICS[metric];
  const row = (s: Season): string => `${s.champion.name}, ${s.year} — ${m.value(s)} over ${s.runnerUp.name}`;
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
      { label: m.largest, text: row(pick(seasons, m.key, 1)) },
      { label: m.smallest, text: row(pick(seasons, m.key, -1)) },
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
