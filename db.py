"""
db.py - Database Access & Query Module for F1 ERA Rescoring Analytics.

Handles SQLite connection pooling, query execution, pandas DataFrame generation,
and Streamlit data caching for historical F1 standings and race data.
"""

import os
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import streamlit as st

# Base Directory & Database Path
BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
DB_PATH: str = os.path.join(BASE_DIR, "f1db.db")

# Standard F1 Team Hex Palette
TEAM_COLORS: Dict[str, str] = {
    "Red Bull": "#3671C6",
    "Red Bull Racing": "#3671C6",
    "Ferrari": "#E8002D",
    "Mercedes": "#27F4D2",
    "McLaren": "#FF8000",
    "Aston Martin": "#229971",
    "Alpine": "#0093CC",
    "Williams": "#64C4FF",
    "RB": "#6692FF",
    "Racing Bulls": "#6692FF",
    "AlphaTauri": "#5E8FAA",
    "Toro Rosso": "#469BFF",
    "Sauber": "#52E252",
    "Alfa Romeo": "#C92D4B",
    "Haas": "#B6BABD",
    "Renault": "#FFF500",
    "Force India": "#F596C8",
    "Racing Point": "#F596C8",
    "Lotus": "#E8C000",
    "Brawn": "#B8FD6E",
    "Benetton": "#008855",
    "Williams-Renault": "#002B66",
    "McLaren-Honda": "#E60000",
    "Tyrrell": "#004080",
    "Brabham": "#002040",
    "Lotus-Climax": "#004225",
}

# Historical F1 Point Systems Mapping
SCORING_SYSTEMS: Dict[str, Optional[Dict[int, float]]] = {
    "Actual Historical Standings": None,
    "Modern System (25-18-15-12-10-8-6-4-2-1)": {
        1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1
    },
    "2003-2009 System (10-8-6-5-4-3-2-1)": {
        1: 10, 2: 8, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1
    },
    "1991-2002 System (10-6-4-3-2-1)": {
        1: 10, 2: 6, 3: 4, 4: 3, 5: 2, 6: 1
    },
    "1950s Classic System (8-6-4-3-2)": {
        1: 8, 2: 6, 3: 4, 4: 3, 5: 2
    },
}

POINTS_REVISIONS: Dict[int, str] = {
    1961: "1961 Revision (9-6-4 System Introduced)",
    1991: "1991 Revision (10-6-4 System / 10pts Win)",
    2003: "2003 Revision (10-8-6 System / Tighter Top 8)",
    2010: "2010 Revision (Modern 25-18-15 System)",
    2019: "2019 Revision (Fastest Lap Point Introduced)",
}


def get_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    Establishes and returns a connection to the SQLite database.
    
    Raises:
        FileNotFoundError: If the database file does not exist at `db_path`.
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found at path: {db_path}")
    return sqlite3.connect(db_path)


def query_actual_standings(conn: sqlite3.Connection) -> pd.DataFrame:
    """Queries official historical driver standings aggregated by season."""
    query = """
    SELECT 
        sds.year AS Season,
        d.id AS DriverId,
        d.first_name || ' ' || d.last_name AS Driver,
        c.name AS Team,
        sds.points AS TotalPoints,
        sds.position_number AS Position
    FROM season_driver_standing sds
    JOIN driver d ON sds.driver_id = d.id
    LEFT JOIN season_entrant_driver sed ON sds.year = sed.year AND sds.driver_id = sed.driver_id
    LEFT JOIN season_entrant_constructor sec ON sed.year = sec.year AND sed.entrant_id = sec.entrant_id
    LEFT JOIN constructor c ON sec.constructor_id = c.id
    ORDER BY sds.year ASC, sds.position_number ASC;
    """
    return pd.read_sql_query(query, conn)


def query_race_results(conn: sqlite3.Connection) -> pd.DataFrame:
    """Queries individual race results required for custom scoring recalculations."""
    query = """
    SELECT 
        r.year AS Season,
        d.id AS DriverId,
        d.first_name || ' ' || d.last_name AS Driver,
        c.name AS Team,
        rd.position_number AS RacePosition
    FROM race_data rd
    JOIN race r ON rd.race_id = r.id
    JOIN driver d ON rd.driver_id = d.id
    LEFT JOIN season_entrant_driver sed ON r.year = sed.year AND rd.driver_id = sed.driver_id
    LEFT JOIN season_entrant_constructor sec ON sed.year = sec.year AND sed.entrant_id = sec.entrant_id
    LEFT JOIN constructor c ON sec.constructor_id = c.id
    WHERE rd.position_number IS NOT NULL
    ORDER BY r.year ASC, r.date ASC;
    """
    return pd.read_sql_query(query, conn)


@st.cache_data(show_spinner="Computing F1 Championship Dominance Data...")
def load_f1_data(selected_scoring_name: str) -> Tuple[pd.DataFrame, Dict[int, pd.DataFrame]]:
    """
    Fetches raw database records, applies the selected scoring scheme (or official standings),
    calculates season title margins, and returns structured data for visualizations.

    Args:
        selected_scoring_name: Key from `SCORING_SYSTEMS`.

    Returns:
        Tuple containing:
            - pd.DataFrame: Season victory margins and dominance metrics.
            - Dict[int, pd.DataFrame]: Top 10 driver standings per season.
    """
    try:
        conn = get_db_connection()
    except FileNotFoundError as e:
        st.error(str(e))
        return pd.DataFrame(), {}

    scoring_map = SCORING_SYSTEMS.get(selected_scoring_name)

    try:
        if scoring_map is None:
            df_raw = query_actual_standings(conn)
        else:
            df_races = query_race_results(conn)
            df_races["SimPoints"] = df_races["RacePosition"].map(scoring_map).fillna(0)
            
            df_agg = (
                df_races.groupby(["Season", "DriverId", "Driver", "Team"])["SimPoints"]
                .sum()
                .reset_index()
                .rename(columns={"SimPoints": "TotalPoints"})
            )
            df_agg["Position"] = (
                df_agg.groupby("Season")["TotalPoints"]
                .rank(method="min", ascending=False)
                .astype(int)
            )
            df_raw = df_agg.sort_values(["Season", "Position"])
    except Exception as e:
        st.error(f"Error querying database: {e}")
        return pd.DataFrame(), {}
    finally:
        conn.close()

    top10_by_season: Dict[int, pd.DataFrame] = {}
    season_margins: List[Dict[str, Any]] = []

    for season, group in df_raw.groupby("Season"):
        clean_rows: List[Dict[str, Any]] = []
        for (driver_id, driver_name), d_group in group.groupby(["DriverId", "Driver"]):
            pos = d_group["Position"].min()
            pts = d_group["TotalPoints"].max()
            teams = [t for t in d_group["Team"].unique() if pd.notna(t)]
            team_str = " / ".join(teams) if teams else "Unknown"
            primary_team = teams[0] if teams else "Unknown"

            clean_rows.append(
                {
                    "DriverId": driver_id,
                    "Driver": driver_name,
                    "Team": team_str,
                    "Primary_Team": primary_team,
                    "TotalPoints": pts,
                    "Position": pos,
                }
            )

        df_season = pd.DataFrame(clean_rows).sort_values("Position").reset_index(drop=True)
        top10_by_season[int(season)] = df_season.head(10).copy()

        p1_rows = df_season[df_season["Position"] == 1]
        p2_rows = df_season[df_season["Position"] == 2]

        if not p1_rows.empty and not p2_rows.empty:
            p1 = p1_rows.iloc[0]
            p2 = p2_rows.iloc[0]

            gap = p1["TotalPoints"] - p2["TotalPoints"]
            pct_gap = (gap / p1["TotalPoints"]) * 100 if p1["TotalPoints"] > 0 else 0

            is_teammate = (p1["Primary_Team"] == p2["Primary_Team"]) and (
                p1["Primary_Team"] != "Unknown"
            )

            teammate_info = "N/A"
            if is_teammate:
                teammate_info = "Runner-Up IS Teammate"
            else:
                same_team_drivers = df_season[
                    (df_season["Primary_Team"] == p1["Primary_Team"])
                    & (df_season["DriverId"] != p1["DriverId"])
                ]
                if not same_team_drivers.empty:
                    best_teammate = same_team_drivers.iloc[0]
                    tm_gap = p1["TotalPoints"] - best_teammate["TotalPoints"]
                    tm_pct = (
                        (tm_gap / p1["TotalPoints"]) * 100
                        if p1["TotalPoints"] > 0
                        else 0
                    )
                    teammate_info = f"{best_teammate['Driver']} (P{int(best_teammate['Position'])}) | Gap: {tm_gap:.1f} pts ({tm_pct:.1f}%)"
                else:
                    teammate_info = "No Teammate Data"

            team_name = p1["Primary_Team"]
            runnerup_team = p2["Primary_Team"]

            champion_color = TEAM_COLORS.get(team_name, "#A0AEC0")
            runnerup_color = TEAM_COLORS.get(runnerup_team, "#A0AEC0")

            season_margins.append(
                {
                    "Season": int(season),
                    "Champion": p1["Driver"],
                    "Champion_Team": team_name,
                    "Champion_Color": champion_color,
                    "Champion_Points": p1["TotalPoints"],
                    "RunnerUp": p2["Driver"],
                    "RunnerUp_Team": runnerup_team,
                    "RunnerUp_Color": runnerup_color,
                    "RunnerUp_Points": p2["TotalPoints"],
                    "Points_Gap": gap,
                    "Pct_Gap": round(pct_gap, 2),
                    "Is_Teammate_Title_Fight": "Yes" if is_teammate else "No",
                    "Teammate_Gap_Info": teammate_info,
                    "Is_Ongoing": True if season == 2026 else False,
                }
            )

    return pd.DataFrame(season_margins), top10_by_season