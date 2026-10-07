import { describe, expect, it } from 'vitest';
import seasonData from '../data/seasons.json';
import { headline, lessFrequentChampionYears, meanPercent, points } from './stats';
import type { Entrant, Season } from './types';

const entrant = (name: string, points: number): Entrant => ({
  driverId: name.toLowerCase(),
  name,
  abbreviation: name.slice(0, 3).toUpperCase(),
  nationality: 'X',
  teamId: 'ferrari',
  teamName: 'Ferrari',
  points,
});
// A season whose gap and 2-decimal percentage follow from the two points totals, as in the pipeline.
const season = (
  year: number,
  championPoints: number,
  runnerUpPoints: number,
  champion = 'A',
  runnerUp = 'B',
): Season => ({
  year,
  champion: entrant(champion, championPoints),
  runnerUp: entrant(runnerUp, runnerUpPoints),
  gapPoints: Math.round((championPoints - runnerUpPoints) * 100) / 100,
  gapPercent: Math.round(((championPoints - runnerUpPoints) / championPoints) * 10000) / 100,
});

// Percentage and points rank these seasons differently: 2000 has the smallest margin
// but not the smallest gap, and 2003 the largest margin but not the largest gap.
const seasons = [
  season(2001, 150, 120, 'Mid'), // 20%, 30 pts
  season(2000, 800, 760, 'Low'), // 5%, 40 pts
  season(2003, 25, 15, 'High', 'Second'), // 40%, 10 pts
  season(2002, 955, 859.5, 'Big'), // 10%, 95.5 pts
];

describe('headline (Margin %)', () => {
  it('ranks by percentage and words it as dominance', () => {
    const h = headline(seasons, 'percent');
    expect(h?.intro).toBe(
      'Across 4 championships (2000–2003), by percentage title margin over the runner-up:',
    );
    expect(h?.rows).toEqual([
      { label: 'Most dominant:', text: 'High, 2003 — 40.00% over Second' },
      { label: 'Closest:', text: 'Low, 2000 — 5.00% over B' },
    ]);
  });

  it('uses a single line for a single season', () => {
    expect(headline([season(2023, 575, 285, 'Champ', 'Second')], 'percent')).toEqual({
      rows: [{ label: '2023 title margin:', text: 'Champ — 50.43% over Second.' }],
    });
  });
});

describe('headline (Points gap)', () => {
  it('ranks by points, formats them exactly, and never says "Most dominant"', () => {
    const h = headline(seasons, 'points');
    expect(h?.intro).toBe(
      'Across 4 championships (2000–2003), by championship points gap over the runner-up:',
    );
    expect(h?.rows).toEqual([
      { label: 'Largest points gap:', text: 'Big, 2002 — 95.5 pts over B' },
      { label: 'Smallest points gap:', text: 'High, 2003 — 10 pts over Second' },
    ]);
    expect(JSON.stringify(h)).not.toContain('Most dominant');
  });

  it('uses a single line for a single season', () => {
    expect(headline([season(2023, 575, 285, 'Champ', 'Second')], 'points')).toEqual({
      rows: [{ label: '2023 points gap:', text: 'Champ — 290 pts over Second.' }],
    });
  });
});

describe('headline', () => {
  it('gives different extremes for the same seasons under each metric', () => {
    const [byPercent, byPoints] = [headline(seasons, 'percent'), headline(seasons, 'points')];
    expect(byPercent?.rows[0]?.text).not.toBe(byPoints?.rows[0]?.text);
    expect(byPercent?.rows[1]?.text).not.toBe(byPoints?.rows[1]?.text);
  });

  it('follows the range: a filtered subset has its own count, span and extremes', () => {
    const h = headline(seasons.filter((s) => s.year >= 2001 && s.year <= 2002), 'percent');
    expect(h?.intro).toContain('Across 2 championships (2001–2002)');
    expect(h?.rows[0]?.text).toContain('Mid, 2001 — 20.00%');
    expect(h?.rows[1]?.text).toContain('Big, 2002 — 10.00%');
  });

  it('keeps the earlier season when extremes tie, under either metric', () => {
    const tied = [season(2005, 100, 60), season(2002, 100, 60), season(2004, 100, 97), season(2001, 100, 97)];
    for (const metric of ['percent', 'points'] as const) {
      const h = headline(tied, metric);
      expect(h?.rows[0]?.text).toContain(', 2002 (tied with 2005) —');
      expect(h?.rows[1]?.text).toContain(', 2001 (tied with 2004) —');
    }
  });

  it('names a genuine percentage tie that is not a points tie', () => {
    // 50% each from different totals; listed out of order to pin the ascending tie list.
    const list = [season(2014, 50, 25), season(2011, 100, 90), season(2012, 200, 100), season(2010, 100, 50)];
    expect(headline(list, 'percent')?.rows).toEqual([
      { label: 'Most dominant:', text: 'A, 2010 (tied with 2012, 2014) — 50.00% over B' },
      { label: 'Closest:', text: 'A, 2011 — 10.00% over B' },
    ]);
    expect(headline(list, 'points')?.rows[0]?.text).toBe('A, 2012 — 100 pts over B');
  });

  it('names a genuine points-gap tie that is not a percentage tie', () => {
    const list = [season(2008, 98, 97), season(2006, 134, 121), season(2007, 110, 109)];
    expect(headline(list, 'points')?.rows[1]?.text).toBe('A, 2007 (tied with 2008) — 1 pt over B');
    expect(headline(list, 'percent')?.rows[1]?.text).toBe('A, 2007 — 0.91% over B');
  });

  it('does not treat margins that only display alike as tied', () => {
    // 33.33% exactly against 33.333…%: both show as 33.33%, but 2001 is genuinely larger.
    const list = [season(2000, 100, 66.67, 'Lesser'), season(2001, 300, 200, 'Greater')];
    expect(list.map((s) => s.gapPercent)).toEqual([33.33, 33.33]);
    expect(headline(list, 'percent')?.rows).toEqual([
      { label: 'Most dominant:', text: 'Greater, 2001 — 33.33% over B' },
      { label: 'Closest:', text: 'Lesser, 2000 — 33.33% over B' },
    ]);
    expect(JSON.stringify(headline(list, 'percent'))).not.toContain('tied with');
  });

  it('names the same season in both rows when every visible season is tied', () => {
    const h = headline([season(2008, 98, 97), season(2007, 110, 109)], 'points');
    expect(h?.rows.map((r) => r.text)).toEqual(Array(2).fill('A, 2007 (tied with 2008) — 1 pt over B'));
  });

  it('returns nothing for no seasons', () => {
    expect(headline([], 'percent')).toBeUndefined();
  });
});

describe('headline (real data)', () => {
  const between = (from: number, to: number): Season[] => seasonData.filter((s) => s.year >= from && s.year <= to);

  it('discloses the 2007 and 2008 one-point gaps in the V8 era', () => {
    expect(headline(between(2006, 2013), 'points')?.rows[1]?.text).toBe(
      'Kimi Räikkönen, 2007 (tied with 2008) — 1 pt over Lewis Hamilton',
    );
  });

  it('recognises 1992 and 1997 as an exactly equal percentage margin', () => {
    // 52/108 and 39/81 are the same fraction, not merely the same rounded 48.15%.
    expect(headline(between(1992, 1997), 'percent')?.rows[0]?.text).toBe(
      'Nigel Mansell, 1992 (tied with 1997) — 48.15% over Riccardo Patrese',
    );
  });
});

describe('meanPercent', () => {
  it('is the arithmetic mean of the margins', () => {
    expect(meanPercent([season(2000, 100, 90), season(2001, 100, 80), season(2002, 100, 64)])).toBe(22);
  });

  it('changes with the selected seasons', () => {
    const all = [season(2000, 100, 90), season(2001, 100, 80), season(2002, 100, 64)];
    expect(meanPercent(all.slice(1))).toBe(28);
  });

  it('equals the value of a single season', () => {
    expect(meanPercent([season(2023, 100, 49.57)])).toBe(50.43);
  });
});

describe('lessFrequentChampionYears', () => {
  // A season won by `driver` for `team`.
  const win = (year: number, driver: string, team = 'ferrari'): Season => ({
    ...season(year, 100, 90, driver),
    champion: { ...entrant(driver, 100), teamId: team },
  });
  const striped = (list: Season[]): number[] => [...lessFrequentChampionYears(list)].sort();

  it('leaves a run won by one driver solid', () => {
    expect(striped([win(2000, 'A'), win(2001, 'A'), win(2002, 'A')])).toEqual([]);
  });

  it('stripes the lower-count driver: 6 vs 1 and 2 vs 1', () => {
    const six = [...[2010, 2011, 2012, 2013, 2014, 2015].map((y) => win(y, 'A')), win(2016, 'B')];
    expect(striped(six)).toEqual([2016]);
    expect(striped([win(1984, 'B'), win(1985, 'A'), win(1986, 'A')])).toEqual([1984]);
  });

  it('keeps a 1 vs 1 run solid', () => {
    expect(striped([win(1992, 'A'), win(1993, 'B')])).toEqual([]);
  });

  it('starts a new run when the constructor changes or the streak is interrupted', () => {
    // A (3) and B (1) for ferrari, then another team, then B alone for ferrari again.
    const list = [win(2000, 'A'), win(2001, 'A'), win(2002, 'A'), win(2003, 'B'), win(2004, 'C', 'mclaren'), win(2005, 'B')];
    expect(striped(list)).toEqual([2003]);
    expect(striped([win(2000, 'A'), win(2001, 'B', 'mclaren'), win(2002, 'B')])).toEqual([]);
    expect(striped([win(2000, 'A'), win(2002, 'B')])).toEqual([]); // a missing year breaks the run
  });

  it('stripes every driver below a unique leader in a three-driver run', () => {
    expect(striped([win(2000, 'A'), win(2001, 'A'), win(2002, 'A'), win(2003, 'B'), win(2004, 'B'), win(2005, 'C')])).toEqual([
      2003, 2004, 2005,
    ]);
  });

  it('keeps tied leaders solid and stripes only the strictly lower ones', () => {
    const list = [win(2000, 'A'), win(2001, 'A'), win(2002, 'B'), win(2003, 'B'), win(2004, 'C')];
    expect(striped(list)).toEqual([2004]);
  });

  it('gives a season the same answer whatever range is visible', () => {
    const all = [win(2000, 'A'), win(2001, 'A'), win(2002, 'B')];
    const full = lessFrequentChampionYears(all);
    // the visible slice is just the 2002 season, but the answer comes from the full dataset
    expect(full.has(2002)).toBe(true);
    expect(lessFrequentChampionYears(all.slice(2)).has(2002)).toBe(false); // a slice alone would lose it
  });
});

describe('lessFrequentChampionYears (real data)', () => {
  const real = (): Set<number> => lessFrequentChampionYears(seasonData);

  it('stripes Lauda 1984, Prost 1989 and Rosberg 2016', () => {
    for (const year of [1984, 1989, 2016]) expect(real().has(year), String(year)).toBe(true);
  });

  it('keeps the Alfa Romeo 1950-51 and Williams 1992-93 ties solid', () => {
    for (const year of [1950, 1951, 1992, 1993]) expect(real().has(year), String(year)).toBe(false);
  });
});

describe('points', () => {
  it('is singular only for exactly 1', () => {
    expect([1, 0.5, 5, 290, 0, 25.14].map(points)).toEqual(['1 pt', '0.5 pts', '5 pts', '290 pts', '0 pts', '25.14 pts']);
  });

  it('is used by the points headline', () => {
    expect(headline([season(2007, 110, 109, 'Raikkonen', 'Hamilton')], 'points')?.rows[0]?.text).toBe('Raikkonen — 1 pt over Hamilton.');
  });
});
