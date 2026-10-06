"""
db.py - Database Access & Query Module for F1 ERA Rescoring Analytics.

Handles SQLite connection pooling, query execution, pandas DataFrame generation,
and Streamlit data caching for historical F1 standings and race data.
"""

import os
import sqlite3
from typing import Dict, Optional, Tuple
import pandas as pd
import streamlit as st

from engine import compute_season_standings

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
    """Establishes and returns a connection to the SQLite database."""
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
    Fetches raw database records and delegates data processing to the pure analytical engine.
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

    return compute_season_standings(df_raw, TEAM_COLORS)