import { NOTES } from './notes';

// Main Grand Prix finishing points: one row per scale, matching the shaded bands.
const SCALES: [seasons: string, points: string][] = [
  ['1950–1959', '8–6–4–3–2 (P1–P5)'],
  ['1960', '8–6–4–3–2–1 (P1–P6)'],
  ['1961–1990', '9–6–4–3–2–1 (P1–P6)'],
  ['1991–2002', '10–6–4–3–2–1 (P1–P6)'],
  ['2003–2009', '10–8–6–5–4–3–2–1 (P1–P8)'],
  ['2010 onwards', '25–18–15–12–10–8–6–4–2–1 (P1–P10)'],
];

export function Methodology({ version }: { version: string }) {
  return (
    <details className="method">
      <summary>How this is measured</summary>
      <p>
        Every title margin is calculated from the champion’s and runner-up’s recorded final
        championship points in F1DB. The title-margin calculation does not reconstruct those
        championship totals race by race. The shaded bands behind the chart are only a visual guide
        to the main Grand Prix finishing-points scale in use at the time; they do not encode every
        scoring rule or exception.
      </p>
      <p>
        <strong>What it measures.</strong> Title-margin dominance = (champion points − runner-up
        points) ÷ champion points × 100, using each season’s recorded final championship standings.
      </p>
      <p>
        <strong>What it does not measure.</strong> Race-win rate, podiums, number of wins, or how
        dominant the car was. In 1952 Alberto Ascari won 6 of his 7 starts, yet his title margin is
        33.33%. His results earned 53.5 points, but only his best results counted towards the
        championship, giving him 36 points to Nino Farina’s 24.
      </p>

      <h3>Scoring Context</h3>
      <h4>Main Grand Prix finishing points</h4>
      <table>
        <thead>
          <tr>
            <th scope="col">Seasons</th>
            <th scope="col">Points By Position</th>
          </tr>
        </thead>
        <tbody>
          {SCALES.map(([seasons, points]) => (
            <tr key={seasons}>
              <td>{seasons}</td>
              <td>{points}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p>
        The chart’s first band covers 1950–1960 because a win was worth 8 points throughout; in
        1960 sixth place began scoring and the fastest-lap point was dropped.
      </p>

      <h4>Other scoring mechanisms</h4>
      <p>
        Other scoring mechanisms are not shown by the bands. Depending on the season or race, they
        could add to, reduce, multiply or split the normal finishing-points allocation: a
        championship point for fastest lap (1950–1959, and 2019–2024 when the fastest-lap driver
        was classified in the top 10), Sprint race points (introduced in 2021: 3–2–1 for the top
        three; from 2022, 8–7–6–5–4–3–2–1 for the top eight), reduced points for shortened races,
        the one-off double points at the 2014 Abu Dhabi Grand Prix, and points split between
        drivers who shared a car in the 1950s. These rules also explain fractional totals: José
        Froilán González’s 25.14 in 1954 includes a seventh of a point, because seven drivers
        shared that year’s British Grand Prix fastest lap.
      </p>

      <h4>Counted championship points</h4>
      <p>
        Separately, until 1990 a driver’s championship total was not simply the sum of their
        results. Under best-results rules, which changed several times, only a set number of each
        driver’s results counted and the rest were dropped. In 1964 Graham Hill’s results earned 41
        points and John Surtees’ 40, but after dropped scores the counted totals were Surtees 40,
        Hill 39, so Surtees was champion. F1 Title Margins always uses the counted totals, here 40
        and 39.
      </p>

      <h4>Ties</h4>
      <p>
        No championship from 1950 to 2025 finished level on points. If one did, the chart would
        show a 0% margin; the recorded champion would be determined by the applicable championship
        tie-break rules.
      </p>

      <h4>Why percentage margin is the default</h4>
      <p>
        Because these scales changed so much, absolute points gaps compare poorly across eras,
        which is why percentage title margin is the default.
      </p>

      <h3>Reading the chart</h3>
      <p>
        <strong>Stripes.</strong> Striped bars mark a less-frequent champion within a consecutive
        run of titles won by the same constructor; the driver with the most titles in that run, or
        tied leaders, stay solid.
      </p>
      <p>
        <strong>Views and the average line.</strong> The era views are curated shortcuts to
        interesting periods, not formal definitions. In Margin (%) mode the dashed line is the
        arithmetic mean of the margins in the selected years.
      </p>
      <p>
        <strong>Season notes.</strong>
      </p>
      <ul>
        {Object.entries(NOTES).map(([year, note]) => (
          <li key={year}>
            {year}: {note}
          </li>
        ))}
      </ul>
      <p>
        <strong>Source.</strong> F1DB {version}, a community-maintained database (
        <a href="https://github.com/f1db/f1db" target="_blank" rel="noreferrer">
          github.com/f1db/f1db
        </a>
        ). Its recorded final standings are treated as this project’s source of truth.
      </p>
    </details>
  );
}
