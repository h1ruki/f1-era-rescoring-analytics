"""Build data/seasons.json (champion vs runner-up margins) from a pinned F1DB release."""

import hashlib
import json
import os
import sqlite3
import sys
import urllib.request
import zipfile
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parent.parent
PIN_PATH = ROOT / "data" / "f1db-release.json"
OUT_PATH = ROOT / "data" / "seasons.json"
CACHE = ROOT / ".cache"
DB_NAME = "f1db.db"
FIRST_YEAR = 1950
CENT = Decimal("0.01")


class Entry(TypedDict):
    driverId: str
    name: str
    nationality: str
    teamId: str
    teamName: str
    points: Decimal


class Season(TypedDict):
    year: int
    champion: Entry
    runnerUp: Entry
    gapPoints: Decimal
    gapPercent: Decimal


def is_completed(champion_flags: int, race_result_counts: list[int]) -> bool:
    """Exactly one champion flagged and every race has at least one RACE_RESULT row."""
    return champion_flags == 1 and all(n > 0 for n in race_result_counts)


def margin(champion: Decimal, runner_up: Decimal) -> tuple[Decimal, Decimal]:
    """Return (gapPoints, gapPercent) rounded to 2 dp; equal points give (0, 0)."""
    if champion < runner_up:
        raise ValueError(f"champion points {champion} below runner-up points {runner_up}")
    if champion == 0:
        raise ValueError("champion has zero points")
    gap = champion - runner_up
    percent = gap / champion * 100
    return gap.quantize(CENT, ROUND_HALF_UP), percent.quantize(CENT, ROUND_HALF_UP)


def pick_team(year: int, driver_id: str, totals: dict[str, Decimal]) -> str:
    """Constructor with the highest race-points sum; an exact top-two tie is an error."""
    if not totals:
        raise ValueError(f"{year} {driver_id}: no race results to attribute a team")
    ranked = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        raise ValueError(f"{year} {driver_id}: tie between {ranked[0][0]} and {ranked[1][0]}")
    return ranked[0][0]


def format_decimal(value: Decimal) -> str:
    """Fixed-point literal: no exponent, trailing zeros removed (40, 395.5, 25.14, 0)."""
    text = format(value, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def to_json(value: Decimal | int | str | list | dict, level: int = 0) -> str:
    """Serialize our fixed shape (dict, list, str, int, Decimal), 2-space indented."""
    if isinstance(value, Decimal):
        return format_decimal(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, int):
        return str(value)
    pad, inner = "  " * level, "  " * (level + 1)
    if isinstance(value, list):
        items, (open_, close) = [f"{inner}{to_json(v, level + 1)}" for v in value], "[]"
    else:
        pairs = ((json.dumps(k, ensure_ascii=False), to_json(v, level + 1)) for k, v in value.items())
        items, (open_, close) = [f"{inner}{k}: {v}" for k, v in pairs], "{}"
    return f"{open_}\n" + ",\n".join(items) + f"\n{pad}{close}"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_database() -> Path:
    pin = json.loads(PIN_PATH.read_text(encoding="utf-8"))
    zip_path = CACHE / pin["asset"]
    CACHE.mkdir(exist_ok=True)
    if not zip_path.exists() or sha256_of(zip_path) != pin["sha256"]:
        url = f"https://github.com/f1db/f1db/releases/download/{pin['version']}/{pin['asset']}"
        tmp = zip_path.with_suffix(".part")
        with urllib.request.urlopen(url) as resp, tmp.open("wb") as f:
            while chunk := resp.read(1 << 20):
                f.write(chunk)
        if sha256_of(tmp) != pin["sha256"]:
            tmp.unlink()
            raise ValueError(f"SHA-256 mismatch for downloaded {pin['asset']}")
        tmp.replace(zip_path)
    db_path = CACHE / DB_NAME
    with zipfile.ZipFile(zip_path) as z, z.open(DB_NAME) as src, db_path.open("wb") as dst:
        while chunk := src.read(1 << 20):
            dst.write(chunk)
    return db_path


def build(conn: sqlite3.Connection) -> list[Season]:
    flags: dict[int, int] = {}
    for (year,) in conn.execute(
        "SELECT year FROM season_driver_standing WHERE championship_won = 1 "
        "ORDER BY year, driver_id"
    ):
        flags[year] = flags.get(year, 0) + 1
    race_counts: dict[int, list[int]] = {}
    for year, n in conn.execute(
        "SELECT r.year, (SELECT COUNT(*) FROM race_data d WHERE d.race_id = r.id "
        "AND d.type = ?) FROM race r ORDER BY r.year, r.id",
        ("RACE_RESULT",),
    ):
        race_counts.setdefault(year, []).append(n)
    team_names = dict(conn.execute("SELECT id, name FROM constructor ORDER BY id"))

    def entry(year: int, position: int) -> tuple[Entry, Decimal]:
        rows = conn.execute(
            "SELECT s.driver_id, d.name, c.name, CAST(s.points AS TEXT) "
            "FROM season_driver_standing s JOIN driver d ON d.id = s.driver_id "
            "LEFT JOIN country c ON c.id = d.nationality_country_id "
            "WHERE s.year = ? AND s.position_number = ? ORDER BY s.driver_id",
            (year, position),
        ).fetchall()
        if len(rows) != 1:
            raise ValueError(f"{year}: expected one driver at position {position}, got {len(rows)}")
        driver_id, name, nationality, points_text = rows[0]
        totals: dict[str, Decimal] = {}
        for team_id, race_points in conn.execute(
            "SELECT d.constructor_id, CAST(COALESCE(d.race_points, 0) AS TEXT) "
            "FROM race_data d JOIN race r ON r.id = d.race_id "
            "WHERE r.year = ? AND d.driver_id = ? AND d.type IN (?, ?) "
            "ORDER BY d.race_id, d.type, d.constructor_id",
            (year, driver_id, "RACE_RESULT", "SPRINT_RACE_RESULT"),
        ):
            totals[team_id] = totals.get(team_id, Decimal(0)) + Decimal(race_points)
        team_id = pick_team(year, driver_id, totals)
        points = Decimal(points_text)
        result = Entry(
            driverId=driver_id,
            name=name,
            nationality=nationality,
            teamId=team_id,
            teamName=team_names.get(team_id, ""),
            points=points,
        )
        return result, points

    seasons: list[Season] = []
    for year in sorted(race_counts):
        if not is_completed(flags.get(year, 0), race_counts[year]):
            continue
        champion, champion_points = entry(year, 1)
        flagged = conn.execute(
            "SELECT driver_id FROM season_driver_standing WHERE year = ? "
            "AND championship_won = 1 ORDER BY driver_id",
            (year,),
        ).fetchone()[0]
        if champion["driverId"] != flagged:
            raise ValueError(f"{year}: championship_won driver is not at position 1")
        runner_up, runner_up_points = entry(year, 2)
        gap, percent = margin(champion_points, runner_up_points)
        seasons.append(
            Season(
                year=year,
                champion=champion,
                runnerUp=runner_up,
                gapPoints=gap,
                gapPercent=percent,
            )
        )
    years = [s["year"] for s in seasons]
    if years != list(range(FIRST_YEAR, FIRST_YEAR + len(years))):
        raise ValueError(f"completed years are not an unbroken run from {FIRST_YEAR}: {years}")
    for s in seasons:
        for who in (s["champion"], s["runnerUp"]):
            for key, value in who.items():
                if key != "points" and not value:
                    raise ValueError(f"{s['year']}: empty {key} for {who['driverId']}")
    return seasons


def main() -> int:
    try:
        db_path = ensure_database()
        with sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True) as conn:
            seasons = build(conn)
    except ValueError as err:
        print(f"build failed: {err}", file=sys.stderr)
        return 1
    tmp = OUT_PATH.with_suffix(".json.tmp")
    tmp.write_text(to_json(seasons) + "\n", encoding="utf-8", newline="\n")
    os.replace(tmp, OUT_PATH)
    print(f"wrote {len(seasons)} seasons to {OUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
