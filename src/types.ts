export interface Entrant {
  driverId: string;
  name: string;
  abbreviation: string; // F1DB driver code, display only
  nationality: string;
  teamId: string;
  teamName: string;
  points: number;
}

export interface Season {
  year: number;
  champion: Entrant;
  runnerUp: Entrant;
  gapPoints: number;
  gapPercent: number;
}

export type Metric = 'percent' | 'points';
export type Orientation = 'vertical' | 'horizontal';
