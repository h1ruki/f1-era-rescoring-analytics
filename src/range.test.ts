import { describe, expect, it } from 'vitest';
import { availableViews, currentView, moveHandle, topHandle } from './range';

const years = Array.from({ length: 76 }, (_, i) => 1950 + i);
const views = availableViews(years);
const view = (id: string) => {
  const found = views.find((v) => v.id === id);
  if (found === undefined) throw new Error(`No view ${id}`);
  return found;
};

describe('view presets', () => {
  it('shows the matching preset for a preset range, first match wins', () => {
    expect(currentView(views, 1950, 2025)?.id).toBe('all');
    expect(currentView(views, 2006, 2013)?.id).toBe('v8');
  });

  it('shows no preset (Custom range) for any other range', () => {
    expect(currentView(views, 2006, 2012)).toBeUndefined();
  });

  it('turns a preset into Custom range after moving either handle one year, and back again', () => {
    const { from, to } = view('v8');
    const [f1, t1] = moveHandle('from', from + 2, from, to);
    expect(currentView(views, f1, t1)).toBeUndefined();
    const [f2, t2] = moveHandle('to', to - 1, from, to);
    expect(currentView(views, f2, t2)).toBeUndefined();
    const [f3, t3] = moveHandle('from', from, f1, t1);
    expect(currentView(views, f3, t3)?.id).toBe('v8');
  });

  it('yields the preset range when selected', () => {
    expect([view('turbo-1').from, view('turbo-1').to]).toEqual([1977, 1988]);
  });

  it('offers presets only: Custom range is never a selectable option', () => {
    expect(views.map((v) => v.id)).not.toContain('custom');
    expect(views).toHaveLength(8);
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
    expect(early).toContain('pioneers');
    expect(early).not.toContain('hybrid');
  });
});

describe('handles', () => {
  it('never cross but may meet on one year', () => {
    expect(moveHandle('from', 2020, 2000, 2010)).toEqual([2010, 2010]);
    expect(moveHandle('to', 1990, 2000, 2010)).toEqual([2000, 2000]);
    expect(moveHandle('from', 2005, 2000, 2010)).toEqual([2005, 2010]);
  });

  it('puts To on top when both handles share the minimum, so To can move right', () => {
    expect(topHandle(1950, 2025)).toBe('to');
  });

  it('puts From on top when both handles share the maximum, so From can move left', () => {
    expect(topHandle(2025, 2025)).toBe('from');
  });

  it('keeps To on top when the handles meet mid-track, where it can move right', () => {
    expect(topHandle(1990, 2025)).toBe('to');
  });
});
