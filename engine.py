"""
engine.py - Core Analytical & Re-Scoring Engine for F1 ERA Analytics.

Contains pure Python calculations for points re-scoring systems, title victory 
margins, teammate gap comparisons, and technical era filtering.
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd


def get_contrast_text_color(hex_color: str) -> str:
    """
    Determines whether black or white text provides optimal contrast against a hex color.

    Args:
        hex_color: Hexadecimal color string (e.g. '#3671C6').

    Returns:
        Hex string for optimal text color ('#0F172A' or '#FFFFFF').
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return "#FFFFFF"
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    # Standard perceived luminance formula
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#0F172A" if luminance > 0.55 else "#FFFFFF"


def get_driver_initials(name: str) -> str:
    """
    Extracts two-letter uppercase initials from a driver's name.

    Args:
        name: Full driver name string.

    Returns:
        Two-character uppercase string.
    """
    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[-1][0]}".upper()
    return name[:2].upper()


def compute_season_standings(
    df_raw: pd.DataFrame, 
    team_colors: Dict[str, str]
) -> Tuple[pd.DataFrame, Dict[int, pd.DataFrame]]:
    """
    Processes raw driver standing records into structured victory margins and 
    per-season top-10 driver rankings.

    Args:
        df_raw: Raw DataFrame from db.py containing Season, DriverId, Driver, Team, 
                TotalPoints, and Position.
        team_colors: Mapping of team names to primary brand hex colors.

    Returns:
        Tuple containing:
            - pd.DataFrame: Calculated victory margins and gap statistics per season.
            - Dict[int, pd.DataFrame]: Top 10 driver standings dictionary keyed by season.
    """
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
            pct_gap = (gap / p1["TotalPoints"]) * 100 if p1["TotalPoints"] > 0 else 0.0

            is_teammate = (p1["Primary_Team"] == p2["Primary_Team"]) and (
                p1["Primary_Team"] != "Unknown"
            )

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
                        else 0.0
                    )
                    teammate_info = (
                        f"{best_teammate['Driver']} (P{int(best_teammate['Position'])}) | "
                        f"Gap: {tm_gap:.1f} pts ({tm_pct:.1f}%)"
                    )
                else:
                    teammate_info = "No Teammate Data"

            team_name = p1["Primary_Team"]
            runnerup_team = p2["Primary_Team"]

            champion_color = team_colors.get(team_name, "#A0AEC0")
            runnerup_color = team_colors.get(runnerup_team, "#A0AEC0")

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


def filter_seasons_by_range(
    df_margins: pd.DataFrame, 
    year_range: Tuple[int, int]
) -> pd.DataFrame:
    """
    Filters the victory margin dataset down to a specific year range and orders by season.

    Args:
        df_margins: Season victory margins DataFrame.
        year_range: Tuple of (start_year, end_year).

    Returns:
        Filtered and sorted pd.DataFrame.
    """
    if df_margins.empty:
        return df_margins

    return (
        df_margins[
            (df_margins["Season"] >= year_range[0])
            & (df_margins["Season"] <= year_range[1])
        ]
        .sort_values("Season")
        .reset_index(drop=True)
    )


def calculate_key_metrics(filtered_df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Calculates key metrics (Most Dominant, Closest Season, Average Gap) for a given filtered dataset.

    Args:
        filtered_df: Filtered victory margins DataFrame.

    Returns:
        Dictionary with metric details or None if DataFrame is empty.
    """
    if filtered_df.empty:
        return None

    most_dominant = filtered_df.loc[filtered_df["Pct_Gap"].idxmax()]
    closest_title = filtered_df.loc[filtered_df["Pct_Gap"].idxmin()]
    avg_gap = filtered_df["Pct_Gap"].mean()

    return {
        "most_dominant_season": int(most_dominant["Season"]),
        "most_dominant_champion": most_dominant["Champion"],
        "most_dominant_gap": most_dominant["Pct_Gap"],
        "closest_season": int(closest_title["Season"]),
        "closest_champion": closest_title["Champion"],
        "closest_gap": closest_title["Pct_Gap"],
        "avg_dominance_margin": round(avg_gap, 1),
    }