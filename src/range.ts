export const CUSTOM = 'custom';
export const CUSTOM_LABEL = 'Custom Range'; // the derived, disabled option shown for a non-preset range
export type Handle = 'from' | 'to';

export interface View {
  id: string;
  label: string;
  from: number;
  to: number;
}

// Curated shortcuts, not formal definitions. The nine eras after All Seasons tile 1950-2025;
// Modern Ground-Effect Era deliberately overlaps Turbo-Hybrid Era.
const PRESETS: readonly View[] = [
  { id: 'all', label: 'All Seasons', from: -Infinity, to: Infinity },
  { id: 'early', label: 'Early Championship Era', from: 1950, to: 1960 },
  { id: 'litre-1.5', label: '1.5-Litre Era', from: 1961, to: 1965 },
  { id: 'litre-3', label: '3-Litre Era', from: 1966, to: 1976 },
  { id: 'turbo-1', label: 'First Turbo Era', from: 1977, to: 1988 },
  { id: 'litre-3.5', label: '3.5-Litre Era', from: 1989, to: 1994 },
  { id: 'litre-3.0', label: '1990s 3-Litre Era', from: 1995, to: 1999 },
  { id: 'v10', label: 'V10 Era', from: 2000, to: 2005 },
  { id: 'v8', label: 'V8 Era', from: 2006, to: 2013 },
  { id: 'hybrid', label: 'Turbo-Hybrid Era', from: 2014, to: 2025 },
  { id: 'ground-effect', label: 'Modern Ground-Effect Era', from: 2022, to: 2025 },
];

// The selectable View options: presets clamped to the available years, empty ones hidden.
export function availableViews(years: readonly number[]): View[] {
  const min = years[0];
  const max = years[years.length - 1];
  if (min === undefined || max === undefined) return [];
  return PRESETS.map((v) => ({ ...v, from: Math.max(v.from, min), to: Math.min(v.to, max) })).filter(
    (v) => v.from <= v.to,
  );
}

// The View shown for a range: the first exact match, otherwise undefined (= "Custom range").
export function currentView(views: readonly View[], from: number, to: number): View | undefined {
  return views.find((v) => v.from === from && v.to === to);
}

// Handles may meet on one year but never cross.
export function moveHandle(handle: Handle, year: number, from: number, to: number): [number, number] {
  return handle === 'from' ? [Math.min(year, to), to] : [from, Math.max(year, from)];
}

// Movement (px) an overlapped press must exceed before it commits to a handle.
export const DEAD_ZONE = 6;

// Which handle a pointer gesture drives. pointerX is where the press started and dx the
// horizontal movement since. A press inside only one handle's hit area picks it; inside
// both (equal or adjacent years) it stays undecided until the pointer leaves the dead
// zone, then left picks From and right picks To; outside both it picks the nearest.
export function pickHandle(
  pointerX: number,
  fromX: number,
  toX: number,
  hitRadius: number,
  dx: number,
): Handle | 'undecided' {
  const [dFrom, dTo] = [Math.abs(pointerX - fromX), Math.abs(pointerX - toX)];
  if (dFrom <= hitRadius && dTo <= hitRadius) {
    return Math.abs(dx) < DEAD_ZONE ? 'undecided' : dx < 0 ? 'from' : 'to';
  }
  if (dFrom <= hitRadius) return 'from';
  if (dTo <= hitRadius) return 'to';
  return dFrom < dTo || (dFrom === dTo && pointerX < fromX) ? 'from' : 'to';
}
