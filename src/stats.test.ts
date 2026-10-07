import { describe, expect, it } from 'vitest';
import { headline } from './stats';
import type { Entrant, Season } from './types';

const entrant = (name: string): Entrant => ({
  driverId: name.toLowerCase(),
  name,
  nationality: 'X',
  teamId: 'ferrari',
  teamName: 'Ferrari',
  points: 1,
});
const season = (year: number, gapPercent: number, champion = 'A'): Season => ({
  year,
  champion: entrant(champion),
  runnerUp: entrant('B'),
  gapPoints: gapPercent,
  gapPercent,
});

describe('headline', () => {
  it('finds the extremes, count and year span from the seasons given', () => {
    const h = headline([season(2001, 20), season(2000, 5), season(2003, 40, 'Z'), season(2002, 10)]);
    expect(h).toMatchObject({ count: 4, firstYear: 2000, lastYear: 2003 });
    expect(h?.most.champion.name).toBe('Z');
    expect(h?.closest.year).toBe(2000);
  });

  it('keeps the earlier season when extremes tie', () => {
    const h = headline([season(2005, 40), season(2002, 40), season(2004, 3), season(2001, 3)]);
    expect(h?.most.year).toBe(2002);
    expect(h?.closest.year).toBe(2001);
  });

  it('returns nothing for no seasons', () => {
    expect(headline([])).toBeUndefined();
  });
});
