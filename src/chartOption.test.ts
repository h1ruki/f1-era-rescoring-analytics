import { describe, expect, it } from 'vitest';
import seasonData from '../data/seasons.json';
import { STRIPES, buildOption, tooltipHtml } from './chartOption';
import { lessFrequentChampionYears } from './stats';
import { FALLBACK_COLOUR, MERCEDES_SILVER, TEAM_COLOURS, teamColour } from './teamColours';
import type { Metric, Orientation, Season } from './types';

const seasons: Season[] = seasonData;
const WIDTH = 1000;
const build = (
  list: Season[],
  metric: Metric,
  orientation: Orientation,
  width = WIDTH,
  striped: ReadonlySet<number> = new Set(),
) => buildOption(list, metric, orientation, width, striped);
const bar = (year: number, metric: Metric) => {
  const index = seasons.findIndex((s) => s.year === year);
  return build(seasons, metric, 'vertical').series[0].data[index];
};
const find = (year: number): Season => {
  const season = seasons.find((s) => s.year === year);
  if (season === undefined) throw new Error(`No season ${year}`);
  return season;
};
const between = (from: number, to: number): Season[] => seasons.filter((s) => s.year >= from && s.year <= to);

describe('buildOption', () => {
  it('uses the metric for the bar value', () => {
    expect(bar(1988, 'percent')?.value).toBe(3.33);
    expect(bar(1988, 'points')?.value).toBe(3);
  });

  it("colours a bar with the champion's team, with no border or outline", () => {
    expect(bar(2025, 'percent')?.itemStyle).toEqual({ color: TEAM_COLOURS['mclaren'] });
    expect(bar(1951, 'percent')?.itemStyle).toEqual({ color: TEAM_COLOURS['alfa-romeo'] });
  });
});

describe('striped bars', () => {
  const fills = (list: Season[], orientation: Orientation, striped: ReadonlySet<number>) =>
    build(list, 'percent', orientation, WIDTH, striped).series[0].data.map((d) => d.itemStyle);

  it('add white diagonal stripes to the listed years without changing the base fill', () => {
    for (const orientation of ['vertical', 'horizontal'] as const) {
      const [solid, striped] = fills(between(2015, 2016), orientation, new Set([2016]));
      const [first, second] = orientation === 'vertical' ? [solid, striped] : [striped, solid];
      expect(first).toEqual({ color: TEAM_COLOURS['mercedes'] });
      expect(second).toEqual({ color: TEAM_COLOURS['mercedes'], decal: STRIPES });
    }
    expect(STRIPES.color).toMatch(/^rgba\(255,255,255,/);
  });

  it('draw the same stripes wherever the year sits in the visible range', () => {
    const striped = lessFrequentChampionYears(seasons); // computed once, from the full dataset
    const [only] = fills(between(2016, 2016), 'vertical', striped);
    const [inContext] = fills(between(2014, 2020), 'vertical', striped).filter((_, i) => i === 2);
    expect(only).toEqual(inContext);
    expect(only?.decal).toBe(STRIPES);
  });
});

describe('tooltipHtml', () => {
  const visible = (html: string): string => html.replace(/<[^>]+>/g, '');

  it('is structured as CHAMPION / RUNNER-UP / MARGIN, without "beat"', () => {
    const html = tooltipHtml(find(1988));
    const order = ['CHAMPION', 'RUNNER-UP', 'MARGIN'].map((h) => html.indexOf(h));
    expect(order.every((i) => i > 0)).toBe(true);
    expect(order).toEqual([...order].sort((a, b) => a - b));
    expect(html).not.toContain('beat');
    expect(html).toMatch(/font-weight:700[^"]*">CHAMPION</);
    expect(visible(html)).toContain('MARGIN3.33% · 3 pts'); // both values, whatever the chart metric
  });

  it('puts the F1DB code before each full name, as "CODE · Full Name (Nationality)"', () => {
    const { champion: c, runnerUp: r } = find(1988);
    const text = visible(tooltipHtml(find(1988)));
    expect(text).toContain(`CHAMPION${c.abbreviation} · Ayrton Senna (Brazil) · McLaren · 90 pts`);
    expect(text).toContain(`RUNNER-UP${r.abbreviation} · Alain Prost (France) · McLaren · 87 pts`);
    expect(tooltipHtml(find(1988))).toContain(`<span style="font-weight:700">${c.abbreviation}</span> · Ayrton Senna`);
  });

  it('escapes names and codes instead of inserting raw HTML', () => {
    const base = find(1988);
    const html = tooltipHtml({
      ...base,
      champion: { ...base.champion, name: '<img src=x>', abbreviation: '<i>', teamName: 'A&B' },
      runnerUp: { ...base.runnerUp, nationality: '<b>' },
    });
    expect(html).not.toContain('<img');
    expect(html).not.toContain('<b>');
    expect(html).not.toContain('<i>');
    expect(html).toContain('&lt;i&gt;');
    expect(html).toContain('&lt;img src=x&gt;');
    expect(html).toContain('A&amp;B');
  });
});

describe('season notes', () => {
  it('adds the 1997 note to that season only, below the structured content', () => {
    const html = tooltipHtml(find(1997));
    expect(html.indexOf('Heinz-Harald Frentzen as P2')).toBeGreaterThan(html.indexOf('MARGIN'));
    expect(tooltipHtml(find(1996))).not.toContain('Frentzen as P2');
  });
});

describe('selected-average line', () => {
  const synthetic = (percents: number[]): Season[] =>
    percents.map((gapPercent, i) => ({ ...find(1988), year: 2000 + i, gapPercent }));
  const average = (list: Season[], metric: Metric, orientation: Orientation) =>
    build(list, metric, orientation).series[0].markLine;

  it('is drawn at the mean margin, labelled to 2 dp, in percentage mode', () => {
    const line = average(synthetic([10, 20, 36.27]), 'percent', 'vertical');
    expect(line?.data).toEqual([{ yAxis: (10 + 20 + 36.27) / 3 }]);
    expect(line?.label?.formatter).toBe('Selected average · 22.09%');
  });

  it('follows the seasons shown and, for one season, equals its margin', () => {
    expect(average(synthetic([10, 20, 30]).slice(1), 'percent', 'vertical')?.data).toEqual([{ yAxis: 25 }]);
    expect(average(synthetic([42.5]), 'percent', 'vertical')?.data).toEqual([{ yAxis: 42.5 }]);
  });

  it('runs along the other axis in the horizontal layout', () => {
    expect(average(synthetic([10, 20]), 'percent', 'horizontal')?.data).toEqual([{ xAxis: 15 }]);
  });

  it('is absent in points mode', () => {
    expect(average(synthetic([10, 20, 30]), 'points', 'vertical')?.data).toEqual([]);
  });
});

describe('driver codes', () => {
  // Plot width at WIDTH is 932px, so 35 bars get 26.6px each and 36 get 25.9px.
  it('are drawn bold above desktop bars only with about 26px or more per bar', () => {
    const few = build(seasons.slice(-35), 'percent', 'vertical').series[0].label;
    expect(few?.show).toBe(true);
    expect(few?.fontWeight).toBe(700);
    expect(build(seasons.slice(-36), 'percent', 'vertical').series[0].label?.show).toBe(false);
    expect(build(seasons, 'percent', 'vertical').series[0].label?.show).toBe(false);
  });

  it('read "year · CODE" on mobile, with the F1DB code and no initials', () => {
    const { yAxis } = build(seasons, 'percent', 'horizontal', 390);
    const labels = JSON.stringify(yAxis).match(/\d{4} · [A-Za-z]+/g) ?? [];
    expect(labels).toHaveLength(seasons.length);
    expect(labels.every((l) => /^\d{4} · [A-Z]{3}$/.test(l))).toBe(true);
    expect(labels).toContain(`2021 · ${find(2021).champion.abbreviation}`);
  });
});

describe('band labels', () => {
  const bandLabels = (list: Season[], orientation: Orientation, width: number): (boolean | undefined)[] =>
    (build(list, 'percent', orientation, width).series[0].markArea?.data ?? []).map((pair) =>
      Array.isArray(pair) ? pair[0]?.label?.show : undefined,
    );

  it('show for both V10-era bands (2000-2005) at desktop width', () => {
    expect(bandLabels(between(2000, 2005), 'vertical', WIDTH)).toEqual([true, true]);
  });

  it('are hidden where the rendered span cannot hold them', () => {
    expect(bandLabels(between(2000, 2005), 'vertical', 120)).toEqual([false, false]); // 3 seasons in ~0px
    expect(bandLabels(between(2000, 2005), 'horizontal', 390)).toEqual([false, false]); // 3 rows x 22px
    expect(bandLabels(seasons, 'horizontal', 390)).toContain(true); // long bands still fit
  });
});

describe('tooltip constructor colours', () => {
  const different = seasons.find((x) => x.champion.teamId !== x.runnerUp.teamId);
  const nameSpan = (html: string, teamName: string): string | undefined =>
    new RegExp(`<span style="color:(#[0-9A-Fa-f]{6});font-weight:600">${teamName}</span>`).exec(html)?.[1];

  it('colours the champion and the runner-up constructor names with their own registry colours', () => {
    if (different === undefined) throw new Error('no season with two different constructors');
    const html = tooltipHtml(different);
    const [champion, runnerUp] = [different.champion, different.runnerUp];
    expect(nameSpan(html, champion.teamName)).toBe(teamColour(champion.teamId, different.year));
    expect(nameSpan(html, runnerUp.teamName)).toBe(teamColour(runnerUp.teamId, different.year));
    expect(teamColour(champion.teamId, different.year)).not.toBe(teamColour(runnerUp.teamId, different.year));
  });

  it('colours the name itself, with only the weight added: no dot, swatch, outline or shadow', () => {
    const html = tooltipHtml(find(1951)); // Alfa Romeo, a dark colour, keeps its exact colour
    expect(html).toContain(`<span style="color:${TEAM_COLOURS['alfa-romeo']};font-weight:600">Alfa Romeo</span>`);
    expect(html).not.toMatch(/background|border|●|shadow|outline|stroke/);
    expect(html.match(/font-weight:600/g)).toHaveLength(2); // one per constructor name
  });

  it('uses silver for Mercedes in 1954-55 and turquoise in the modern era', () => {
    expect(nameSpan(tooltipHtml(find(1954)), 'Mercedes')).toBe(MERCEDES_SILVER);
    expect(nameSpan(tooltipHtml(find(2014)), 'Mercedes')).toBe(TEAM_COLOURS['mercedes']);
  });

  it('takes the colour from the registry, using the fallback for an unknown team', () => {
    const base = find(1988);
    const html = tooltipHtml({ ...base, champion: { ...base.champion, teamId: 'unknown-team', teamName: 'Newcomer' } });
    expect(nameSpan(html, 'Newcomer')).toBe(FALLBACK_COLOUR);
  });

  it('still escapes team names, and a colour cannot come from data text', () => {
    const base = find(1988);
    const html = tooltipHtml({
      ...base,
      champion: { ...base.champion, teamId: 'red"><script>', teamName: '<b>X&Y</b>' },
    });
    expect(html).toContain('&lt;b&gt;X&amp;Y&lt;/b&gt;</span>');
    expect(html).not.toContain('<script>');
    expect(html).toContain(`color:${FALLBACK_COLOUR}`);
  });
});

describe('bar labels', () => {
  it('keep the same label in the hover (emphasis) state, so the code never vanishes', () => {
    for (const orientation of ['vertical', 'horizontal'] as const) {
      const [series] = build(seasons.slice(-12), 'percent', orientation, 390).series;
      expect(series.emphasis?.label).toBe(series.label);
    }
    // a dense range keeps its codes hidden when hovered, too
    const dense = build(seasons, 'percent', 'vertical').series[0];
    expect(dense.emphasis?.label?.show).toBe(false);
  });
});

describe('singular point unit', () => {
  it('reads "1 pt" in the tooltip margin row and "pts" elsewhere', () => {
    const text = tooltipHtml(find(2007)).replace(/<[^>]+>/g, '');
    expect(text).toContain('MARGIN0.91% · 1 pt');
    expect(text).not.toContain('1 pts');
    expect(text).toContain('110 pts');
  });
});
