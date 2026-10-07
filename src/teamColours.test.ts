import { describe, expect, it } from 'vitest';
import seasonData from '../data/seasons.json';
import { contrastRatio } from './contrast';
import { CHART_BACKGROUND, TEAM_COLOURS } from './teamColours';

describe('team colours', () => {
  it('has a colour for every champion team in the data', () => {
    const missing = new Set(
      seasonData.map((s) => s.champion.teamId).filter((id) => !(id in TEAM_COLOURS)),
    );
    expect([...missing]).toEqual([]);
  });

  it('reaches 3:1 contrast against the chart background', () => {
    for (const [teamId, colour] of Object.entries(TEAM_COLOURS)) {
      expect(contrastRatio(colour, CHART_BACKGROUND), teamId).toBeGreaterThanOrEqual(3);
    }
  });
});
