import { NOTES } from './notes';

export function Methodology({ version }: { version: string }) {
  return (
    <details className="method">
      <summary>How this is measured</summary>
      <p>
        <strong>What it measures.</strong> Title-margin dominance = (champion points − runner-up
        points) ÷ champion points × 100, using each season’s recorded final championship standings.
      </p>
      <p>
        <strong>What it does not measure.</strong> Race-win rate, podiums, number of wins, or how
        dominant the car was. In 1952 Alberto Ascari won 6 of his 7 starts, yet his title margin is
        33.33%, because only a driver’s best results counted that season.
      </p>
      <p>
        <strong>Dropped scores.</strong> Before 1991, Formula 1 used various best-results
        (dropped-score) rules, and the exact rule changed over time. In 1964 Graham Hill scored 41
        points to John Surtees’ 40, but with only the best results counting, Surtees won the title
        40 to 39.
      </p>
      <p>
        <strong>Points as recorded.</strong> Points include historical fractional points. For
        example, José Froilán González’s 25.14 in 1954 includes a fraction of the fastest-lap point
        from the British Grand Prix, where seven drivers shared the fastest lap. Shared drives and
        shortened half-points races could also produce fractional championship points historically.
        Equal points would show a 0% margin, resolved by countback; no title has been decided that
        way.
      </p>
      <p>
        <strong>Bands and views.</strong> The shaded background bands show the main Grand Prix
        finishing-points scale only, not every scoring rule. The era views are curated shortcuts to
        interesting periods, not formal definitions.
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
