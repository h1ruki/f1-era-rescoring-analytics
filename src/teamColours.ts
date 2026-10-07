// The one palette registry, keyed by F1DB teamId: one exact identity colour per constructor,
// used for the bars and for the constructor names in the tooltip. Every champion and
// runner-up team in the data needs an entry (see teamColours.test.ts); add one line when a
// new team appears.
export const CHART_BACKGROUND = '#0B0C0F';
export const TOOLTIP_BACKGROUND = '#000000';

// Shown for a team that has no explicit entry (the coverage test keeps this from shipping).
export const FALLBACK_COLOUR = '#8B919A';

export const TEAM_COLOURS: Record<string, string> = {
  // Reds
  ferrari: '#E80020',
  'alfa-romeo': '#971B29',
  // Orange / yellow / gold
  mclaren: '#FF8000',
  brabham: '#B8860B',
  renault: '#F7B100',
  brawn: '#C8FF00',
  march: '#F05A28',
  // Greens
  cooper: '#006B54',
  lotus: '#004225',
  brm: '#4B5D52',
  benetton: '#008860',
  vanwall: '#4CAF50',
  // Blues
  'red-bull': '#3671C6',
  williams: '#64C4FF',
  maserati: '#0C2340',
  matra: '#318CE7',
  tyrrell: '#003B73',
  wolf: '#6F8FE8',
  // Silver / turquoise: the modern Petronas colour; see MERCEDES_SILVER for 1954-55
  mercedes: '#27F4D2',
};

// The 1954-55 Mercedes were silver. This is the one historical exception to the registry.
export const MERCEDES_SILVER = '#BFC3C7';

export const hasTeamColour = (teamId: string): boolean => Object.hasOwn(TEAM_COLOURS, teamId);

export function teamColour(teamId: string, year: number): string {
  if (teamId === 'mercedes' && year >= 1954 && year <= 1955) return MERCEDES_SILVER;
  return (hasTeamColour(teamId) ? TEAM_COLOURS[teamId] : undefined) ?? FALLBACK_COLOUR;
}
