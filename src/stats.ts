import type { Season } from './types';

export interface Headline {
  count: number;
  firstYear: number;
  lastYear: number;
  most: Season;
  closest: Season;
}

// Extremes by gapPercent; a tie keeps the earlier season.
function pick(seasons: readonly Season[], direction: 1 | -1): Season {
  return seasons.reduce((best, s) =>
    (s.gapPercent - best.gapPercent) * direction > 0 ||
    (s.gapPercent === best.gapPercent && s.year < best.year)
      ? s
      : best,
  );
}

export function headline(seasons: readonly Season[]): Headline | undefined {
  if (seasons.length === 0) return undefined;
  const years = seasons.map((s) => s.year);
  return {
    count: seasons.length,
    firstYear: Math.min(...years),
    lastYear: Math.max(...years),
    most: pick(seasons, 1),
    closest: pick(seasons, -1),
  };
}
