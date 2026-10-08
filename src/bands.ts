// Main Grand Prix finishing-points scale only: not every historical scoring rule. "Points to P6"
// means finishing points were awarded down to sixth place, not that six results counted.
export interface Band {
  from: number;
  to: number | null; // null = open-ended, up to the latest season
  label: string;
}

export const BANDS: readonly Band[] = [
  { from: 1950, to: 1960, label: 'Win = 8 pts' },
  { from: 1961, to: 1990, label: 'Win = 9 pts · Points to P6' },
  { from: 1991, to: 2002, label: 'Win = 10 pts · Points to P6' },
  { from: 2003, to: 2009, label: 'Win = 10 pts · Points to P8' },
  { from: 2010, to: null, label: 'Win = 25 pts · Points to P10' },
];

export interface VisibleBand {
  label: string;
  first: number;
  last: number;
  tone: number; // index in BANDS, so shading stays stable when the range changes
}

// Bands clipped to the given years.
export function visibleBands(years: readonly number[]): VisibleBand[] {
  return BANDS.flatMap((b, tone) => {
    const inside = years.filter((y) => y >= b.from && (b.to === null || y <= b.to));
    const first = inside[0];
    const last = inside[inside.length - 1];
    return first === undefined || last === undefined ? [] : [{ label: b.label, first, last, tone }];
  });
}
