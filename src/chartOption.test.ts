import { describe, expect, it } from 'vitest';
import seasonData from '../data/seasons.json';
import { buildOption, tooltipHtml } from './chartOption';
import { TEAM_COLOURS } from './teamColours';
import type { Season } from './types';

const seasons: Season[] = seasonData;
const bar = (year: number, metric: 'percent' | 'points') => {
  const index = seasons.findIndex((s) => s.year === year);
  return buildOption(seasons, metric, 'vertical').series[0].data[index];
};
const find = (year: number): Season => {
  const season = seasons.find((s) => s.year === year);
  if (season === undefined) throw new Error(`No season ${year}`);
  return season;
};

describe('buildOption', () => {
  it('uses the metric for the bar value', () => {
    expect(bar(1988, 'percent')?.value).toBe(3.33);
    expect(bar(1988, 'points')?.value).toBe(3);
  });

  it("colours a bar with the champion's team", () => {
    expect(bar(2025, 'percent')?.itemStyle.color).toBe(TEAM_COLOURS['mclaren']);
  });
});

describe('tooltipHtml', () => {
  it('shows both drivers and the 2dp margin', () => {
    const html = tooltipHtml(find(1988));
    expect(html).toContain('Ayrton Senna (Brazil) · McLaren · 90 pts');
    expect(html).toContain('beat Alain Prost (France) · McLaren · 87 pts');
    expect(html).toContain('Margin 3.33% · 3 pts');
  });

  it('escapes names instead of inserting raw HTML', () => {
    const base = find(1988);
    const html = tooltipHtml({
      ...base,
      champion: { ...base.champion, name: '<img src=x>', teamName: 'A&B' },
      runnerUp: { ...base.runnerUp, nationality: '<b>' },
    });
    expect(html).not.toContain('<img');
    expect(html).not.toContain('<b>');
    expect(html).toContain('&lt;img src=x&gt;');
    expect(html).toContain('A&amp;B');
  });
});
