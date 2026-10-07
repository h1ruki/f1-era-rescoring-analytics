import { useEffect, useRef, useState } from 'react';
import { init, use } from 'echarts/core';
import type { ECharts } from 'echarts/core';
import { BarChart } from 'echarts/charts';
import { GridComponent, MarkAreaComponent, MarkLineComponent, TooltipComponent } from 'echarts/components';
import { SVGRenderer } from 'echarts/renderers';
import { MARGIN, ROW_HEIGHT, buildOption } from './chartOption';
import type { Metric, Orientation, Season } from './types';

use([BarChart, GridComponent, MarkAreaComponent, MarkLineComponent, TooltipComponent, SVGRenderer]);

interface Props {
  seasons: readonly Season[];
  metric: Metric;
  orientation: Orientation;
  striped: ReadonlySet<number>;
  label: string;
}

export function Chart({ seasons, metric, orientation, striped, label }: Props) {
  const el = useRef<HTMLDivElement>(null);
  const chart = useRef<ECharts | null>(null);
  const lastOrientation = useRef<Orientation | null>(null);
  const [width, setWidth] = useState(0);

  useEffect(() => {
    if (el.current === null) return;
    const instance = init(el.current, undefined, { renderer: 'svg' });
    chart.current = instance;
    const observer = new ResizeObserver((entries) => {
      instance.resize();
      setWidth(Math.round(entries[0]?.contentRect.width ?? 0));
    });
    observer.observe(el.current);
    return () => {
      observer.disconnect();
      instance.dispose();
      chart.current = null;
      lastOrientation.current = null;
    };
  }, []);

  useEffect(() => {
    if (width === 0) return; // wait for the first measurement
    // Merge keeps bars animating between metrics; an orientation change swaps
    // the axes entirely, so it replaces the option instead.
    chart.current?.resize();
    chart.current?.setOption(
      buildOption(seasons, metric, orientation, width, striped),
      lastOrientation.current !== orientation,
    );
    lastOrientation.current = orientation;
  }, [seasons, metric, orientation, width, striped]);

  const { top, bottom } = MARGIN.horizontal;
  const height = orientation === 'horizontal' ? seasons.length * ROW_HEIGHT + top + bottom : undefined;
  return <div ref={el} className="chart" role="img" aria-label={label} style={{ height }} />;
}
