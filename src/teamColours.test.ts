import { describe, expect, it } from 'vitest';
import seasonData from '../data/seasons.json';
import { FALLBACK_COLOUR, MERCEDES_SILVER, TEAM_COLOURS, hasTeamColour, teamColour } from './teamColours';

describe('team colours', () => {
  it('holds the exact locked identity colours', () => {
    expect(TEAM_COLOURS).toEqual({
      ferrari: '#E80020',
      'alfa-romeo': '#971B29',
      mclaren: '#FF8000',
      brabham: '#B8860B',
      renault: '#F7B100',
      brawn: '#C8FF00',
      march: '#F05A28',
      cooper: '#006B54',
      lotus: '#004225',
      brm: '#4B5D52',
      benetton: '#008860',
      vanwall: '#4CAF50',
      'red-bull': '#3671C6',
      williams: '#64C4FF',
      maserati: '#0C2340',
      matra: '#318CE7',
      tyrrell: '#003B73',
      wolf: '#6F8FE8',
      mercedes: '#27F4D2',
    });
    expect(MERCEDES_SILVER).toBe('#BFC3C7');
  });

  it('resolves every champion and runner-up team and year to an explicit colour', () => {
    for (const s of seasonData) {
      for (const { teamId } of [s.champion, s.runnerUp]) {
        expect(hasTeamColour(teamId), `${s.year} ${teamId}`).toBe(true);
        expect(teamColour(teamId, s.year), `${s.year} ${teamId}`).not.toBe(FALLBACK_COLOUR);
      }
    }
  });

  it('falls back to a neutral colour for an unknown team, and says it is not explicit', () => {
    expect(hasTeamColour('some-future-team')).toBe(false);
    expect(hasTeamColour('constructor')).toBe(false);
    expect(teamColour('some-future-team', 2030)).toBe(FALLBACK_COLOUR);
    expect(teamColour('constructor', 2030)).toBe(FALLBACK_COLOUR);
  });

  it('uses silver for Mercedes in 1954 and 1955 only, and leaves every other team alone', () => {
    expect(teamColour('mercedes', 1954)).toBe(MERCEDES_SILVER);
    expect(teamColour('mercedes', 1955)).toBe(MERCEDES_SILVER);
    expect(teamColour('mercedes', 1953)).toBe(TEAM_COLOURS['mercedes']);
    expect(teamColour('mercedes', 1956)).toBe(TEAM_COLOURS['mercedes']);
    expect(teamColour('mercedes', 2020)).toBe('#27F4D2');
    for (const [teamId, colour] of Object.entries(TEAM_COLOURS)) {
      if (teamId !== 'mercedes') expect(teamColour(teamId, 1954), teamId).toBe(colour);
    }
  });
});
