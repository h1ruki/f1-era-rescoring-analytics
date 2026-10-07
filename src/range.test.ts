import { describe, expect, it } from 'vitest';
import { CUSTOM_LABEL, DEAD_ZONE, availableViews, currentView, moveHandle, pickHandle } from './range';

const years = Array.from({ length: 76 }, (_, i) => 1950 + i);
const views = availableViews(years);
const view = (id: string) => {
  const found = views.find((v) => v.id === id);
  if (found === undefined) throw new Error(`No view ${id}`);
  return found;
};
const shown = (from: number, to: number): string => currentView(views, from, to)?.label ?? CUSTOM_LABEL;

describe('view presets', () => {
  it('has exactly these labels, ranges and order', () => {
    expect(views.map((v) => [v.label, v.from, v.to])).toEqual([
      ['All Seasons', 1950, 2025],
      ['Early Championship Era', 1950, 1960],
      ['1.5-Litre Era', 1961, 1965],
      ['3-Litre Era', 1966, 1976],
      ['First Turbo Era', 1977, 1988],
      ['3.5-Litre Era', 1989, 1994],
      ['3.0-Litre Era', 1995, 1999],
      ['V10 Era', 2000, 2005],
      ['V8 Era', 2006, 2013],
      ['Turbo-Hybrid Era', 2014, 2025],
      ['Modern Ground-Effect Era', 2022, 2025],
    ]);
  });

  it('puts All Seasons first, equal to the full available range, whatever that range is', () => {
    for (const available of [years, years.slice(0, 40), [...years, 2026, 2027]]) {
      const [first] = availableViews(available);
      expect(first?.label).toBe('All Seasons');
      expect([first?.from, first?.to]).toEqual([available[0], available[available.length - 1]]);
    }
  });

  it('tiles 1950-2025 with the nine eras, no gaps and no overlaps (fixed endpoints)', () => {
    const nine = views.slice(1, 10);
    expect(nine).toHaveLength(9);
    expect(nine[0]?.from).toBe(1950);
    expect(nine[8]?.to).toBe(2025);
    nine.slice(1).forEach((v, i) => expect(v.from).toBe((nine[i]?.to ?? NaN) + 1));
  });

  it('overlaps Turbo-Hybrid Era with Modern Ground-Effect Era on purpose', () => {
    const [hybrid, modern] = [view('hybrid'), view('ground-effect')];
    expect(modern.label).toBe('Modern Ground-Effect Era');
    expect(modern.from).toBeGreaterThan(hybrid.from);
    expect(modern.from).toBeLessThanOrEqual(hybrid.to);
    expect(modern.to).toBe(hybrid.to);
  });

  it('shows the matching preset for a preset range, first match wins', () => {
    expect(shown(1950, 2025)).toBe('All Seasons');
    expect(shown(2006, 2013)).toBe('V8 Era');
    expect(shown(2022, 2025)).toBe('Modern Ground-Effect Era');
    expect(shown(2014, 2025)).toBe('Turbo-Hybrid Era');
  });

  it('shows Custom Range for any other range', () => {
    expect(currentView(views, 2006, 2012)).toBeUndefined();
    expect(shown(2006, 2012)).toBe('Custom Range');
  });

  it('goes preset -> Custom Range -> exact preset boundaries -> the preset label again', () => {
    for (const v of views) {
      if (v.to === v.from) continue;
      const [f1, t1] = moveHandle('to', v.to - 1, v.from, v.to);
      expect(shown(f1, t1), `${v.label} moved`).toBe(CUSTOM_LABEL);
      const [f2, t2] = moveHandle('to', v.to, f1, t1);
      expect(shown(f2, t2), v.label).toBe(shown(v.from, v.to));
    }
    expect(shown(1950, 2024)).toBe('Custom Range');
    expect(shown(1950, 2025)).toBe('All Seasons'); // the full range restores All Seasons
  });

  it('keeps the exact capitalisation of every displayed label', () => {
    expect(CUSTOM_LABEL).toBe('Custom Range');
    for (const v of views) expect(v.label).toMatch(/^[A-Z0-9]/);
    expect(views.map((v) => v.label)).not.toContain(CUSTOM_LABEL);
  });

  it('offers presets only: Custom Range is never a selectable option', () => {
    expect(views.map((v) => v.id)).not.toContain('custom');
    expect(views).toHaveLength(11);
  });

  it('clamps every preset to the available years and hides empty ones', () => {
    for (const available of [years, years.slice(0, 40), years.slice(30, 64)]) {
      const min = available[0] ?? 0;
      const max = available[available.length - 1] ?? 0;
      for (const v of availableViews(available)) {
        expect(v.from).toBeLessThanOrEqual(v.to);
        expect(v.from).toBeGreaterThanOrEqual(min);
        expect(v.to).toBeLessThanOrEqual(max);
      }
    }
    const early = availableViews(years.slice(0, 15)).map((v) => v.id); // 1950-1964
    expect(early).toContain('early');
    expect(early).not.toContain('hybrid');
  });
});

describe('handles', () => {
  it('never cross but may meet on one year', () => {
    expect(moveHandle('from', 2020, 2000, 2010)).toEqual([2010, 2010]);
    expect(moveHandle('to', 1990, 2000, 2010)).toEqual([2000, 2000]);
    expect(moveHandle('from', 2005, 2000, 2010)).toEqual([2005, 2010]);
  });
});

describe('pickHandle', () => {
  const R = 22;
  const far = DEAD_ZONE + 4;

  it('picks the handle whose hit area holds the press when only one does', () => {
    expect(pickHandle(100, 100, 300, R, 0)).toBe('from');
    expect(pickHandle(300, 100, 300, R, 0)).toBe('to');
    expect(pickHandle(120, 100, 300, R, 0)).toBe('from');
  });

  it('stays undecided when the press is in both hit areas and has not left the dead zone', () => {
    expect(pickHandle(100, 100, 110, R, 0)).toBe('undecided');
    expect(pickHandle(100, 100, 110, R, DEAD_ZONE - 1)).toBe('undecided');
    expect(pickHandle(100, 100, 110, R, -(DEAD_ZONE - 1))).toBe('undecided');
  });

  it('resolves an overlapped press by direction: left picks From, right picks To', () => {
    expect(pickHandle(100, 100, 110, R, -far)).toBe('from');
    expect(pickHandle(100, 100, 110, R, far)).toBe('to');
    expect(pickHandle(100, 100, 110, R, -DEAD_ZONE)).toBe('from');
    expect(pickHandle(100, 100, 110, R, DEAD_ZONE)).toBe('to');
  });

  it('treats equal positions like overlapping ones', () => {
    expect(pickHandle(100, 100, 100, R, 0)).toBe('undecided');
    expect(pickHandle(100, 100, 100, R, -far)).toBe('from');
    expect(pickHandle(100, 100, 100, R, far)).toBe('to');
  });

  it('picks the nearest handle when the press is outside both hit areas', () => {
    expect(pickHandle(170, 100, 300, R, 0)).toBe('from');
    expect(pickHandle(230, 100, 300, R, 0)).toBe('to');
    expect(pickHandle(10, 100, 300, R, 0)).toBe('from');
    expect(pickHandle(400, 100, 300, R, 0)).toBe('to');
  });

  it('keeps ties outside equal positions on the side of the press', () => {
    expect(pickHandle(20, 100, 100, R, 0)).toBe('from');
    expect(pickHandle(180, 100, 100, R, 0)).toBe('to');
  });
});
