import type { BarSeriesOption } from 'echarts/charts';
import type { EChartsCoreOption } from 'echarts/core';
import type { Entrant, Metric, Orientation, Season } from './types';
import { visibleBands } from './bands';
import { NOTES } from './notes';
import { meanPercent, percent, points } from './stats';
import { CHART_BACKGROUND, TOOLTIP_BACKGROUND, teamColour } from './teamColours';

export const ROW_HEIGHT = 22; // px per season in the horizontal layout
const FONT = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
const TEXT = '#8b919a';
const GRID = '#1b1f26';
const MIN_CODE_PX = 26; // minimum width per bar before driver codes are drawn above the bars
const BAND_LABEL_CHAR_PX = 5.6; // estimated width of one band-label character at 10px
const BAND_LABEL_PAD = 10;
type BandArea = Extract<NonNullable<BarSeriesOption['markArea']>['data'], unknown[]>[number];

// Grid margins, set here rather than measured so the plot size is known exactly: they
// leave room for the axis labels outside the plot.
export const MARGIN = {
  vertical: { left: 52, right: 16, top: 22, bottom: 28 },
  horizontal: { left: 78, right: 44, top: 28, bottom: 24 },
};

// White diagonal lines drawn over a bar's own fill (ECharts' native decal): the mark of a
// less-frequent champion within a run of titles for the same constructor.
export const STRIPES = {
  symbol: 'rect',
  symbolSize: 1,
  rotation: Math.PI / 4,
  dashArrayX: [1, 0],
  dashArrayY: [2, 4],
  color: 'rgba(255,255,255,0.55)',
} as const;

export interface BarDatum {
  value: number;
  itemStyle: { color: string; decal?: typeof STRIPES };
}
export type ChartOption = EChartsCoreOption & {
  series: [Omit<BarSeriesOption, 'data'> & { data: BarDatum[] }];
};

export function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

const axisValue = (v: number, metric: Metric): string => (metric === 'percent' ? `${v}%` : `${v}`);

const SUBHEADING = `margin-top:6px;font-size:10px;font-weight:700;letter-spacing:0.08em;color:${TEXT}`;

// Each row reads "CODE · Full Name (Nationality) · Constructor · points". The constructor name
// is in its exact registry colour (never from data text).
export function tooltipHtml(s: Season): string {
  const team = (e: Entrant): string =>
    `<span style="color:${teamColour(e.teamId, s.year)};font-weight:600">${escapeHtml(e.teamName)}</span>`;
  const line = (e: Entrant): string =>
    `<div class="tip-row"><span style="font-weight:700">${escapeHtml(e.abbreviation)}</span> · ${escapeHtml(e.name)} (${escapeHtml(e.nationality)}) · ${team(e)} · ${points(e.points)}</div>`;
  const heading = (text: string): string => `<div style="${SUBHEADING}">${text}</div>`;
  const note = NOTES[s.year];
  return [
    `<strong>${s.year}</strong>`,
    heading('CHAMPION'),
    line(s.champion),
    heading('RUNNER-UP'),
    line(s.runnerUp),
    heading('MARGIN'),
    `<div class="tip-row">${percent(s)} · ${points(s.gapPoints)}</div>`,
    ...(note === undefined ? [] : [`<div class="tip-note" style="margin-top:6px;color:${TEXT}">${escapeHtml(note)}</div>`]),
  ].join('');
}

// Label every year when few are shown, otherwise every 5th or 10th.
const labelStep = (count: number): number => (count <= 15 ? 1 : count <= 40 ? 5 : 10);

export function buildOption(
  input: readonly Season[],
  metric: Metric,
  orientation: Orientation,
  width: number, // chart width in px
  striped: ReadonlySet<number>, // years of less-frequent champions, from the full dataset
): ChartOption {
  const horizontal = orientation === 'horizontal';
  const margin = MARGIN[orientation];
  // Category axes run bottom-to-top, so reverse the rows to put 1950 at the top.
  const seasons = horizontal ? [...input].reverse() : input;
  const years = seasons.map((s) => s.year);
  const step = labelStep(years.length);
  // The one plot-size calculation: pixels along the category axis per season.
  const pxPerSeason = horizontal ? ROW_HEIGHT : (width - margin.left - margin.right) / seasons.length;
  const category = {
    type: 'category' as const,
    // Mobile rows read "2023 · VER"; the desktop axis keeps plain years.
    data: horizontal ? seasons.map((s) => `${s.year} · ${s.champion.abbreviation}`) : years.map(String),
    axisLine: { lineStyle: { color: GRID } },
    axisTick: { show: false, interval: 0 }, // markArea snaps to ticks, so keep one per season
    axisLabel: {
      color: TEXT,
      fontSize: 11,
      interval: horizontal ? 0 : (_: number, year: string) => Number(year) % step === 0,
      // Mobile "2023 · VER": the year in normal weight, the code bold.
      formatter: horizontal ? (row: string) => row.replace(/ · (.*)$/, ' · {code|$1}') : undefined,
      rich: { code: { fontWeight: 700 } },
    },
  };
  const value = {
    type: 'value' as const,
    position: horizontal ? ('top' as const) : ('left' as const),
    boundaryGap: [0, '15%'] as [number, string], // headroom above the tallest bar for its code and the band labels
    axisLabel: { color: TEXT, fontSize: 11, formatter: (v: number) => axisValue(v, metric) },
    splitLine: { lineStyle: { color: GRID } },
  };
  // Shaded points-scale bands, from the first bar to the last (bar markAreas snap to ticks).
  // A band's label shows only when its rendered span fits the label.
  const bands = visibleBands(input.map((s) => s.year)).map((b): BandArea => {
    const [i, j] = [years.indexOf(b.first), years.indexOf(b.last)];
    const [a, z] = [Math.min(i, j), Math.max(i, j)];
    const text = horizontal ? b.label : b.label.replace(' · ', '\n');
    const textPx = Math.max(...text.split('\n').map((l) => l.length)) * BAND_LABEL_CHAR_PX + BAND_LABEL_PAD;
    const label = {
      show: (b.last - b.first + 1) * pxPerSeason >= textPx,
      position: horizontal ? ('insideRight' as const) : ('insideTop' as const),
      rotate: horizontal ? 90 : 0,
      formatter: text,
    };
    const itemStyle = { color: b.tone % 2 === 0 ? 'rgba(255,255,255,0.045)' : 'rgba(255,255,255,0.015)' };
    return horizontal
      ? [{ yAxis: a, itemStyle, label }, { yAxis: z }]
      : [{ xAxis: a, itemStyle, label }, { xAxis: z }];
  });

  // Mobile: the value at the end of each bar. Desktop: the champion's F1DB driver code above
  // it, when there is room. The emphasis (hover) state is given the same label: ECharts does
  // not carry it over, and the code would vanish while the bar is hovered.
  const barLabel = {
    show: horizontal || pxPerSeason >= MIN_CODE_PX,
    position: horizontal ? ('right' as const) : ('top' as const),
    color: horizontal ? '#a9afb9' : TEXT,
    fontSize: horizontal ? 11 : 10,
    fontWeight: horizontal ? 400 : 700,
    formatter: ({ dataIndex }: { dataIndex: number }): string => {
      const s = seasons[dataIndex];
      if (s === undefined) return '';
      if (!horizontal) return s.champion.abbreviation;
      return metric === 'percent' ? percent(s) : `${s.gapPoints}`;
    },
  };

  // Dashed reference line at the visible seasons' mean margin; percentage mode only.
  const mean = metric === 'percent' ? meanPercent(seasons) : undefined;
  const average = mean === undefined ? [] : [horizontal ? { xAxis: mean } : { yAxis: mean }];

  return {
    backgroundColor: CHART_BACKGROUND,
    textStyle: { fontFamily: FONT },
    animationDurationUpdate: 700,
    animationEasingUpdate: 'cubicInOut',
    grid: margin,
    xAxis: horizontal ? value : category,
    yAxis: horizontal ? category : value,
    tooltip: {
      trigger: 'axis',
      confine: true,
      axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(255,255,255,0.06)' } },
      backgroundColor: TOOLTIP_BACKGROUND,
      borderColor: '#343a44',
      padding: horizontal ? 7 : 10,
      textStyle: { color: '#d7dae0', fontSize: horizontal ? 11 : 12, lineHeight: horizontal ? 16 : 18 },
      // Mobile: contained in the viewport, so driver rows may wrap. Desktop: no width cap; the
      // rows stay on one line (styles.css) and the box widens to fit them.
      extraCssText: horizontal ? 'white-space: normal; max-width: min(340px, 92vw);' : 'white-space: normal;',
      formatter: (params: { dataIndex: number } | { dataIndex: number }[]): string => {
        const first = Array.isArray(params) ? params[0] : params;
        const season = first === undefined ? undefined : seasons[first.dataIndex];
        return season === undefined ? '' : tooltipHtml(season);
      },
    },
    series: [
      {
        type: 'bar',
        barCategoryGap: '28%',
        barMaxWidth: 48,
        itemStyle: { borderRadius: horizontal ? [0, 2, 2, 0] : [2, 2, 0, 0] },
        label: barLabel,
        emphasis: { label: barLabel }, // hovering must not drop the label
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { type: 'dashed', width: 1, color: TEXT, opacity: 0.8 },
          label: {
            color: '#c4c9d1',
            fontSize: 10,
            // Below the plot in the horizontal layout, where the line spans the full height.
            position: horizontal ? 'start' : 'insideEndTop',
            textBorderColor: CHART_BACKGROUND, // keeps it legible where it crosses a bar
            textBorderWidth: 3,
            formatter: mean === undefined ? '' : `Selected average · ${mean.toFixed(2)}%`,
          },
          data: average,
        },
        markArea: {
          silent: true,
          label: { color: '#6f7580', fontSize: 10, lineHeight: 12 },
          data: bands,
        },
        data: seasons.map((s) => {
          const color = teamColour(s.champion.teamId, s.year);
          return {
            value: metric === 'percent' ? s.gapPercent : s.gapPoints,
            // The exact constructor fill; a less-frequent champion in a run also gets stripes.
            itemStyle: striped.has(s.year) ? { color, decal: STRIPES } : { color },
          };
        }),
      },
    ],
  };
}
