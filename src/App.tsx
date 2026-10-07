import { useEffect, useMemo, useState } from 'react';
import seasonData from '../data/seasons.json';
import release from '../data/f1db-release.json';
import { Chart } from './Chart';
import { Controls } from './Controls';
import { Methodology } from './Methodology';
import { headline } from './stats';
import type { Metric, Orientation, Season } from './types';

const seasons: Season[] = seasonData;
const years = seasons.map((s) => s.year);
const WIDE = window.matchMedia('(min-width: 640px)');
const OPTIONS: { metric: Metric; text: string }[] = [
  { metric: 'percent', text: 'Margin (%)' },
  { metric: 'points', text: 'Points gap' },
];

function useOrientation(): Orientation {
  const [wide, setWide] = useState(WIDE.matches);
  useEffect(() => {
    const onChange = () => setWide(WIDE.matches);
    WIDE.addEventListener('change', onChange);
    return () => WIDE.removeEventListener('change', onChange);
  }, []);
  return wide ? 'vertical' : 'horizontal';
}

export function App() {
  const [metric, setMetric] = useState<Metric>('percent');
  const [fromYear, setFromYear] = useState(years[0] ?? 0);
  const [toYear, setToYear] = useState(years[years.length - 1] ?? 0);
  const orientation = useOrientation();
  const visible = useMemo(
    () => seasons.filter((s) => s.year >= fromYear && s.year <= toYear),
    [fromYear, toYear],
  );
  const stat = headline(seasons); // all seasons: independent of metric and range
  const what = metric === 'percent' ? 'percentage margin' : 'points gap';
  const label = `Bar chart of the ${what} between the champion and runner-up in each F1 season from ${fromYear} to ${toYear}. Bars are coloured by the champion's team. Select a bar for details.`;
  const row = (title: string, s: Season) => (
    <p>
      <span>{title}</span> {s.champion.name}, {s.year} – {s.gapPercent.toFixed(2)}% over{' '}
      {s.runnerUp.name}
    </p>
  );

  return (
    <main>
      <h1>F1 Title Margins</h1>
      <p className="subtitle">How dominant was each F1 champion in their title-winning season?</p>
      {stat && (
        <div className="stat">
          <p className="stat-intro">
            Across {stat.count} championships ({stat.firstYear}–{stat.lastYear}), by percentage title
            margin over the runner-up:
          </p>
          {row('Most dominant:', stat.most)}
          {row('Closest:', stat.closest)}
        </div>
      )}
      <div className="toggle" role="group" aria-label="Metric">
        {OPTIONS.map((o) => (
          <button
            key={o.metric}
            type="button"
            aria-pressed={metric === o.metric}
            onClick={() => setMetric(o.metric)}
          >
            {o.text}
          </button>
        ))}
      </div>
      <Controls
        years={years}
        from={fromYear}
        to={toYear}
        onChange={(from, to) => {
          setFromYear(from);
          setToYear(to);
        }}
      />
      <Chart seasons={visible} metric={metric} orientation={orientation} label={label} />
      <Methodology version={release.version} />
      <footer>Data: F1DB {release.version} · recorded final standings</footer>
    </main>
  );
}
