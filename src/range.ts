export const CUSTOM = 'custom';
export type Handle = 'from' | 'to';

export interface View {
  id: string;
  label: string;
  from: number;
  to: number;
}

// Curated shortcuts, not formal definitions. Overlaps are intentional.
const PRESETS: readonly View[] = [
  { id: 'all', label: 'All seasons', from: -Infinity, to: Infinity },
  { id: 'pioneers', label: '1950s pioneers', from: 1950, to: 1959 },
  { id: 'litre-1.5', label: '1.5-litre era', from: 1961, to: 1965 },
  { id: 'turbo-1', label: 'First turbo era', from: 1977, to: 1988 },
  { id: 'v10', label: 'V10 era', from: 2000, to: 2005 },
  { id: 'v8', label: 'V8 era', from: 2006, to: 2013 },
  { id: 'hybrid', label: 'Turbo-hybrid era', from: 2014, to: 2025 },
  { id: 'ground-effect', label: 'Ground-effect era', from: 2022, to: 2025 },
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

// Which of the two stacked range inputs sits on top. When both handles share the
// maximum, From must be on top so it can move left; otherwise To is on top, which
// also covers the shared minimum (To can move right).
export function topHandle(from: number, max: number): Handle {
  return from >= max ? 'from' : 'to';
}
