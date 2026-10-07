import { describe, expect, it } from 'vitest';
import { BANDS, visibleBands } from './bands';

describe('points-scale bands', () => {
  it('start at 1950, are contiguous, and the last is open-ended', () => {
    expect(BANDS[0]?.from).toBe(1950);
    BANDS.slice(1).forEach((band, i) => {
      expect(band.from).toBe((BANDS[i]?.to ?? NaN) + 1);
    });
    expect(BANDS[BANDS.length - 1]?.to).toBeNull();
  });

  it('are clipped to the visible years', () => {
    const years = Array.from({ length: 8 }, (_, i) => 2006 + i); // 2006-2013
    const clipped = visibleBands(years).map((b) => [b.first, b.last]);
    expect(clipped).toEqual([
      [2006, 2009],
      [2010, 2013],
    ]);
  });
});
