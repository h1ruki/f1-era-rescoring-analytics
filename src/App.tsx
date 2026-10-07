import { useEffect, useState } from 'react';
import seasonData from '../data/seasons.json';
import release from '../data/f1db-release.json';
import { Chart } from './Chart';
import type { Metric, Orientation, Season } from './types';

const seasons: Season[] = seasonData;
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
  const orientation = useOrientation();
  const first = seasons[0]?.year;
  const last = seasons[seasons.length - 1]?.year;
  const what = metric === 'percent' ? 'percentage margin' : 'points gap';
  const label = `Bar chart of the ${what} between the champion and runner-up in each F1 season from ${first} to ${last}. Bars are coloured by the champion's team. Select a bar for details.`;

  return (
    <main>
      <h1>F1 Title Margins</h1>
      <p className="subtitle">How dominant was each F1 champion in their title-winning season?</p>
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
      <Chart seasons={seasons} metric={metric} orientation={orientation} label={label} />
      <footer>Data: F1DB {release.version} · recorded final standings</footer>
    </main>
  );
}
