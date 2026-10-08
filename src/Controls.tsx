import { useRef } from 'react';
import type { PointerEvent } from 'react';
import { CUSTOM, CUSTOM_LABEL, DEAD_ZONE, availableViews, currentView, moveHandle, pickHandle } from './range';
import type { Handle } from './range';

const THUMB = 44; // touch target in px; keep in sync with --thumb in styles.css
const HIT_RADIUS = THUMB / 2;

interface Props {
  years: readonly number[];
  from: number;
  to: number;
  onChange: (from: number, to: number) => void;
}

// Transient state of the pointer gesture in progress (never rendered).
interface Gesture {
  startX: number;
  startY: number;
  handle?: Handle; // undefined while an overlapped press is still undecided
  offset: number; // keeps the thumb under the finger at the point it was grabbed
}

// fromYear/toYear (owned by the parent) are the only state: View, the dropdowns and the
// slider all read them, and every control writes them back through onChange.
export function Controls({ years, from, to, onChange }: Props) {
  const gesture = useRef<Gesture | null>(null);
  const min = years[0] ?? from;
  const max = years[years.length - 1] ?? to;
  const views = availableViews(years);
  const move = (handle: Handle, year: number) => onChange(...moveHandle(handle, year, from, to));
  const fraction = (year: number) => (year - min) / Math.max(max - min, 1);

  // One handler drives both thumbs; the native range inputs only provide keyboard and
  // screen-reader access (they ignore the pointer), so stacking order never matters.
  const drive = (e: PointerEvent<HTMLDivElement>, released = false) => {
    const g = gesture.current;
    if (g === null) return;
    const { left, width } = e.currentTarget.getBoundingClientRect();
    const span = Math.max(width - THUMB, 1);
    const xOf = (year: number) => THUMB / 2 + span * fraction(year);
    const x = e.clientX - left;
    if (g.handle === undefined) {
      // Commit only to a deliberate horizontal movement (or a release, for a tap on the
      // track); the first jitter of a vertical swipe must not move anything.
      const dx = x - g.startX;
      const horizontal = Math.abs(dx) >= DEAD_ZONE && Math.abs(dx) > Math.abs(e.clientY - g.startY);
      if (!horizontal && !released) return;
      const picked = pickHandle(g.startX, xOf(from), xOf(to), HIT_RADIUS, dx);
      if (picked === 'undecided') return;
      const thumbX = xOf(picked === 'from' ? from : to);
      g.handle = picked;
      g.offset = Math.abs(g.startX - thumbX) <= HIT_RADIUS ? thumbX - g.startX : 0;
    }
    const year = Math.round(min + ((x + g.offset - THUMB / 2) / span) * (max - min));
    move(g.handle, Math.min(max, Math.max(min, year)));
  };
  // Nothing changes on press: a touch that turns into a vertical scroll is cancelled by the
  // browser before it moves, and a plain tap on the track applies on release.
  const press = (e: PointerEvent<HTMLDivElement>) => {
    e.currentTarget.setPointerCapture(e.pointerId);
    const { left } = e.currentTarget.getBoundingClientRect();
    gesture.current = { startX: e.clientX - left, startY: e.clientY, offset: 0 };
  };
  const release = (e: PointerEvent<HTMLDivElement>) => {
    drive(e, true);
    gesture.current = null;
  };

  const thumb = (handle: Handle, value: number, label: string) => (
    <input
      type="range"
      aria-label={label}
      min={min}
      max={max}
      step={1}
      value={value}
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
              {CUSTOM_LABEL}
            </option>
          </select>
        </label>
        {yearSelect('from', 'From', from, years.filter((y) => y <= to))}
        {yearSelect('to', 'To', to, years.filter((y) => y >= from))}
      </div>
      <div
        className="slider"
        onPointerDown={press}
        onPointerMove={(e) => drive(e)}
        onPointerUp={release}
        onPointerCancel={() => (gesture.current = null)}
      >
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
