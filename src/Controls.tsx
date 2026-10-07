import { CUSTOM, availableViews, currentView, moveHandle, topHandle } from './range';
import type { Handle } from './range';

interface Props {
  years: readonly number[];
  from: number;
  to: number;
  onChange: (from: number, to: number) => void;
}

// fromYear/toYear (owned by the parent) are the only state: View, the dropdowns and the
// slider all read them, and every control writes them back through onChange.
export function Controls({ years, from, to, onChange }: Props) {
  const min = years[0] ?? from;
  const max = years[years.length - 1] ?? to;
  const views = availableViews(years);
  const move = (handle: Handle, year: number) => onChange(...moveHandle(handle, year, from, to));
  const fraction = (year: number) => (year - min) / Math.max(max - min, 1);
  const thumb = (handle: Handle, value: number, label: string) => (
    <input
      type="range"
      aria-label={label}
      min={min}
      max={max}
      step={1}
      value={value}
      style={{ zIndex: topHandle(from, max) === handle ? 2 : 1 }}
      onChange={(e) => move(handle, Number(e.target.value))}
    />
  );
  const yearSelect = (handle: Handle, label: string, value: number, options: number[]) => (
    <label>
      {label}
      <select value={value} onChange={(e) => move(handle, Number(e.target.value))}>
        {options.map((y) => (
          <option key={y}>{y}</option>
        ))}
      </select>
    </label>
  );

  return (
    <section className="range" aria-label="Year range">
      <div className="selects">
        <label className="view">
          View
          <select
            value={currentView(views, from, to)?.id ?? CUSTOM}
            onChange={(e) => {
              const view = views.find((v) => v.id === e.target.value);
              if (view !== undefined) onChange(view.from, view.to);
            }}
          >
            {views.map((v) => (
              <option key={v.id} value={v.id}>
                {v.label}
              </option>
            ))}
            <option value={CUSTOM} disabled>
              Custom range
            </option>
          </select>
        </label>
        {yearSelect('from', 'From', from, years.filter((y) => y <= to))}
        {yearSelect('to', 'To', to, years.filter((y) => y >= from))}
      </div>
      <div className="slider">
        <div
          className="band"
          style={{
            left: `calc(var(--thumb) / 2 + (100% - var(--thumb)) * ${fraction(from)})`,
            right: `calc(var(--thumb) / 2 + (100% - var(--thumb)) * ${1 - fraction(to)})`,
          }}
        />
        {thumb('from', from, 'From year')}
        {thumb('to', to, 'To year')}
      </div>
      <p className="range-text">
        {from} – {to}
      </p>
    </section>
  );
}
