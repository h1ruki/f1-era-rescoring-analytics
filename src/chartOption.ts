import type { BarSeriesOption } from 'echarts/charts';
import type { EChartsCoreOption } from 'echarts/core';
import type { Metric, Orientation, Season } from './types';
import { visibleBands } from './bands';
import { NOTES } from './notes';
import { CHART_BACKGROUND, teamColour } from './teamColours';

export const ROW_HEIGHT = 22; // px per season in the horizontal layout
const FONT = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
const TEXT = '#8b919a';
const GRID = '#1b1f26';
const MIN_BAND_LABEL_SEASONS = 6;
type BandArea = Extract<NonNullable<BarSeriesOption['markArea']>['data'], unknown[]>[number];

export interface BarDatum {
  value: number;
  itemStyle: { color: string };
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

const percent = (s: Season): string => `${s.gapPercent.toFixed(2)}%`;
const axisValue = (v: number, metric: Metric): string => (metric === 'percent' ? `${v}%` : `${v}`);

export function tooltipHtml(s: Season): string {
  const { champion: c, runnerUp: r } = s;
  const line = (e: Season['champion']): string =>
    `${escapeHtml(e.name)} (${escapeHtml(e.nationality)}) · ${escapeHtml(e.teamName)} · ${e.points} pts`;
  const note = NOTES[s.year];
  return [
    `<strong>${s.year}</strong>`,
    line(c),
    `beat ${line(r)}`,
    `Margin ${percent(s)} · ${s.gapPoints} pts`,
    ...(note === undefined ? [] : [`<span style="color:${TEXT}">${escapeHtml(note)}</span>`]),
  ].join('<br/>');
}

// Label every year when few are shown, otherwise every 5th or 10th.
const labelStep = (count: number): number => (count <= 15 ? 1 : count <= 40 ? 5 : 10);

export function buildOption(
  input: readonly Season[],
  metric: Metric,
  orientation: Orientation,
): ChartOption {
  const horizontal = orientation === 'horizontal';
  // Category axes run bottom-to-top, so reverse the rows to put 1950 at the top.
  const seasons = horizontal ? [...input].reverse() : input;
  const years = seasons.map((s) => s.year);
  const step = labelStep(years.length);
  const category = {
    type: 'category' as const,
    data: years.map(String),
    axisLine: { lineStyle: { color: GRID } },
    axisTick: { show: false, interval: 0 }, // markArea snaps to ticks, so keep one per season
    axisLabel: {
      color: TEXT,
      fontSize: 11,
      interval: horizontal ? 0 : (_: number, year: string) => Number(year) % step === 0,
    },
  };
  const value = {
    type: 'value' as const,
    position: horizontal ? ('top' as const) : ('left' as const),
    axisLabel: { color: TEXT, fontSize: 11, formatter: (v: number) => axisValue(v, metric) },
    splitLine: { lineStyle: { color: GRID } },
  };
  // Shaded points-scale bands, from the first bar to the last (bar markAreas snap to ticks).
  const bands = visibleBands(input.map((s) => s.year)).map((b): BandArea => {
    const [i, j] = [years.indexOf(b.first), years.indexOf(b.last)];
    const [a, z] = [Math.min(i, j), Math.max(i, j)];
    const label = {
      show: b.last - b.first + 1 >= MIN_BAND_LABEL_SEASONS,
      position: horizontal ? ('insideRight' as const) : ('insideTop' as const),
      rotate: horizontal ? 90 : 0,
      formatter: horizontal ? b.label : b.label.replace(' · ', '\n'),
    };
    const itemStyle = { color: b.tone % 2 === 0 ? 'rgba(255,255,255,0.045)' : 'rgba(255,255,255,0.015)' };
    return horizontal
      ? [{ yAxis: a, itemStyle, label }, { yAxis: z }]
      : [{ xAxis: a, itemStyle, label }, { xAxis: z }];
  });

  return {
    backgroundColor: CHART_BACKGROUND,
    textStyle: { fontFamily: FONT },
    animationDurationUpdate: 700,
    animationEasingUpdate: 'cubicInOut',
    grid: {
      left: 12,
      right: horizontal ? 44 : 16,
      top: horizontal ? 28 : 16,
      bottom: 8,
      outerBoundsMode: 'same',
      outerBoundsContain: 'axisLabel',
    },
    xAxis: horizontal ? value : category,
    yAxis: horizontal ? category : value,
    tooltip: {
      trigger: 'axis',
      confine: true,
      axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(255,255,255,0.06)' } },
      backgroundColor: '#14171c',
      borderColor: '#2a2f38',
      padding: horizontal ? 7 : 10,
      textStyle: { color: '#d7dae0', fontSize: horizontal ? 11 : 12, lineHeight: horizontal ? 16 : 18 },
      extraCssText: 'white-space: normal; max-width: min(340px, 92vw);',
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
        label: {
          show: horizontal,
          position: 'right',
          color: '#a9afb9',
          fontSize: 11,
          formatter: ({ dataIndex }: { dataIndex: number }): string => {
            const s = seasons[dataIndex];
            return s === undefined ? '' : metric === 'percent' ? percent(s) : `${s.gapPoints}`;
          },
        },
        markArea: {
          silent: true,
          label: { color: '#6f7580', fontSize: 10, lineHeight: 12 },
          data: bands,
        },
        data: seasons.map((s) => ({
          value: metric === 'percent' ? s.gapPercent : s.gapPoints,
          itemStyle: { color: teamColour(s.champion.teamId) },
        })),
      },
    ],
  };
}
