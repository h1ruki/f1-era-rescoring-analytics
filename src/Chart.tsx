import { useEffect, useRef } from 'react';
import { init, use } from 'echarts/core';
import type { ECharts } from 'echarts/core';
import { BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent } from 'echarts/components';
import { SVGRenderer } from 'echarts/renderers';
import { ROW_HEIGHT, buildOption } from './chartOption';
import type { Metric, Orientation, Season } from './types';

use([BarChart, GridComponent, TooltipComponent, SVGRenderer]);

interface Props {
  seasons: readonly Season[];
  metric: Metric;
  orientation: Orientation;
  label: string;
}

export function Chart({ seasons, metric, orientation, label }: Props) {
  const el = useRef<HTMLDivElement>(null);
  const chart = useRef<ECharts | null>(null);
  const lastOrientation = useRef<Orientation | null>(null);

  useEffect(() => {
    if (el.current === null) return;
    const instance = init(el.current, undefined, { renderer: 'svg' });
    chart.current = instance;
    const observer = new ResizeObserver(() => instance.resize());
    observer.observe(el.current);
    return () => {
      observer.disconnect();
      instance.dispose();
      chart.current = null;
      lastOrientation.current = null;
    };
  }, []);

  useEffect(() => {
    // Merge keeps bars animating between metrics; an orientation change swaps
    // the axes entirely, so it replaces the option instead.
    chart.current?.resize();
    chart.current?.setOption(
      buildOption(seasons, metric, orientation),
      lastOrientation.current !== orientation,
    );
    lastOrientation.current = orientation;
  }, [seasons, metric, orientation]);

  const height = orientation === 'horizontal' ? seasons.length * ROW_HEIGHT + 44 : undefined;
  return <div ref={el} className="chart" role="img" aria-label={label} style={{ height }} />;
}
