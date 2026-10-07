// One colour per champion team, used for every season. Every value must reach
// 3:1 contrast against CHART_BACKGROUND (enforced in teamColours.test.ts).
export const CHART_BACKGROUND = '#0B0C0F';

export const TEAM_COLOURS: Record<string, string> = {
  // Reds
  ferrari: '#E8002D',
  'alfa-romeo': '#B83A3A', // brick red, darker and duller than Ferrari
  maserati: '#B0506A', // burgundy, lifted to wine-rose to pass 3:1
  // Orange / yellow / gold
  mclaren: '#FF8000',
  lotus: '#C99A2E', // JPS gold
  renault: '#FFF500',
  brawn: '#C6F31E', // fluorescent yellow-green
  // Greens
  cooper: '#2E9B5E', // British racing green, lifted
  brm: '#8F9A3C', // warm olive
  benetton: '#12D6B4', // bright green-teal
  // Blues
  'red-bull': '#3671C6',
  williams: '#64C4FF',
  matra: '#5568F0', // French blue, pushed towards ultramarine
  tyrrell: '#2A8FBD', // Elf blue, pushed towards cyan
  // Silver / white
  mercedes: '#BFC3C7',
  brabham: '#FFFFFF', // white
};

export function teamColour(teamId: string): string {
  const colour = TEAM_COLOURS[teamId];
  if (colour === undefined) throw new Error(`No colour for team "${teamId}"`);
  return colour;
}
