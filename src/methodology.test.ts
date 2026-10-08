import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { Methodology } from './Methodology';

const html = renderToStaticMarkup(createElement(Methodology, { version: 'v-test' }));
const text = html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ');

describe('methodology scoring copy', () => {
  it('keeps the four concepts apart: finishing points, other mechanisms, counted points, the margin', () => {
    for (const heading of ['Main Grand Prix finishing points', 'Other scoring mechanisms', 'Counted championship points']) {
      expect(html).toContain(`<h4>${heading}</h4>`);
    }
    expect(text).toContain('does not reconstruct those championship totals race by race');
    expect(text).toContain('F1 Title Margins always uses the counted totals, here 40 and 39');
  });

  it('shows the six finishing-point scales in a two-column table', () => {
    expect(html).toContain('<th scope="col">Seasons</th><th scope="col">Points By Position</th>');
    for (const row of [
      ['1950–1959', '8–6–4–3–2 (P1–P5)'],
      ['1960', '8–6–4–3–2–1 (P1–P6)'],
      ['1961–1990', '9–6–4–3–2–1 (P1–P6)'],
      ['1991–2002', '10–6–4–3–2–1 (P1–P6)'],
      ['2003–2009', '10–8–6–5–4–3–2–1 (P1–P8)'],
      ['2010 onwards', '25–18–15–12–10–8–6–4–2–1 (P1–P10)'],
    ]) {
      expect(html).toContain(`<tr><td>${row[0]}</td><td>${row[1]}</td></tr>`);
    }
  });

  it('separates points earned from points counted, and does not claim a universal countback', () => {
    expect(text).toContain('His results earned 53.5 points, but only his best results counted towards the championship, giving him 36 points to Nino Farina’s 24');
    expect(text).toContain('classified in the top 10');
    expect(text).not.toContain('finished in the top 10');
    expect(text).not.toMatch(/countback/i);
    expect(text).toContain('applicable championship tie-break rules');
  });

  it('keeps the approved non-scoring content', () => {
    for (const phrase of ['Striped bars mark a less-frequent champion', 'dashed line is the arithmetic mean', 'Heinz-Harald Frentzen as P2', 'F1DB v-test', 'github.com/f1db/f1db', 'licensed under CC BY 4.0']) {
      expect(text).toContain(phrase);
    }
  });
});
