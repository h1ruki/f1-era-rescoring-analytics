"""
engine.py - Core Analytical & Re-Scoring Engine for F1 ERA Analytics.

Contains pure Python and vectorized pandas calculations for points re-scoring 
systems, title victory margins, teammate gap comparisons, and technical era filtering.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
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
    per-season top-10 driver rankings using vectorized pandas operations.

    Args:
        df_raw: Raw DataFrame containing Season, DriverId, Driver, Team, TotalPoints, Position.
        team_colors: Mapping of team names to primary brand hex colors.

    Returns:
        Tuple containing:
            - pd.DataFrame: Calculated victory margins and gap statistics per season.
            - Dict[int, pd.DataFrame]: Top 10 driver standings dictionary keyed by season.
    """
    if df_raw.empty:
        return pd.DataFrame(), {}

    # 1. Vectorized aggregation per driver per season
    df_clean = (
        df_raw.groupby(["Season", "DriverId", "Driver"], as_index=False)
        .agg(
            Position=("Position", "min"),
            TotalPoints=("TotalPoints", "max"),
            Primary_Team=("Team", lambda x: x.dropna().iloc[0] if not x.dropna().empty else "Unknown"),
            Team=("Team", lambda x: " / ".join(x.dropna().unique()) if not x.dropna().empty else "Unknown"),
        )
        .sort_values(["Season", "Position"])
        .reset_index(drop=True)
    )

    # 2. Extract Top 10 standings per season
    top10_dict = {
        int(season): group.head(10).copy().reset_index(drop=True)
        for season, group in df_clean.groupby("Season")
    }

    # 3. Vectorized P1 (Champion) and P2 (Runner-Up) extraction
    p1_df = df_clean[df_clean["Position"] == 1].copy()
    p2_df = df_clean[df_clean["Position"] == 2].copy()

    merged = pd.merge(
        p1_df,
        p2_df,
        on="Season",
        suffixes=("_P1", "_P2"),
        how="inner",
    )

    if merged.empty:
        return pd.DataFrame(), top10_dict

    # Vectorized gap calculations
    merged["Points_Gap"] = merged["TotalPoints_P1"] - merged["TotalPoints_P2"]
    merged["Pct_Gap"] = np.where(
        merged["TotalPoints_P1"] > 0,
        (merged["Points_Gap"] / merged["TotalPoints_P1"]) * 100,
        0.0,
    ).round(2)

    merged["Is_Teammate"] = (
        (merged["Primary_Team_P1"] == merged["Primary_Team_P2"])
        & (merged["Primary_Team_P1"] != "Unknown")
    )

    # 4. Process Teammate Gap Information for Non-Teammate Title Fights
    non_teammate_p1s = merged[~merged["Is_Teammate"]][["Season", "DriverId_P1", "Primary_Team_P1", "TotalPoints_P1"]]
    
    # Match P1 drivers with their actual teammates in the same season
    tm_merged = pd.merge(
        df_clean,
        non_teammate_p1s,
        left_on=["Season", "Primary_Team"],
        right_on=["Season", "Primary_Team_P1"],
    )
    tm_candidates = tm_merged[tm_merged["DriverId"] != tm_merged["DriverId_P1"]].sort_values(
        ["Season", "Position"]
    )
    best_teammates = tm_candidates.groupby("Season").first().reset_index()

    teammate_info_map = {}
    for _, row in best_teammates.iterrows():
        season = row["Season"]
        p1_pts = row["TotalPoints_P1"]
        tm_gap = p1_pts - row["TotalPoints"]
        tm_pct = (tm_gap / p1_pts * 100) if p1_pts > 0 else 0.0
        teammate_info_map[season] = (
            f"{row['Driver']} (P{int(row['Position'])}) | Gap: {tm_gap:.1f} pts ({tm_pct:.1f}%)"
        )

    # 5. Build output dataset
    season_margins = []
    for _, row in merged.iterrows():
        season = int(row["Season"])
        is_tm = row["Is_Teammate"]
        
        if is_tm:
            tm_info = "Runner-Up IS Teammate"
        else:
            tm_info = teammate_info_map.get(season, "No Teammate Data")

        c_team = row["Primary_Team_P1"]
        r_team = row["Primary_Team_P2"]

        season_margins.append(
            {
                "Season": season,
                "Champion": row["Driver_P1"],
                "Champion_Team": c_team,
                "Champion_Color": team_colors.get(c_team, "#A0AEC0"),
                "Champion_Points": row["TotalPoints_P1"],
                "RunnerUp": row["Driver_P2"],
                "RunnerUp_Team": r_team,
                "RunnerUp_Color": team_colors.get(r_team, "#A0AEC0"),
                "RunnerUp_Points": row["TotalPoints_P2"],
                "Points_Gap": row["Points_Gap"],
                "Pct_Gap": row["Pct_Gap"],
                "Is_Teammate_Title_Fight": "Yes" if is_tm else "No",
                "Teammate_Gap_Info": tm_info,
                "Is_Ongoing": season == 2026,
            }
        )

    return pd.DataFrame(season_margins), top10_dict


def filter_seasons_by_range(
    df_margins: pd.DataFrame, 
    year_range: Tuple[int, int]
) -> pd.DataFrame:
    """Filters the victory margin dataset down to a specific year range."""
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
    """Calculates key metrics for a given filtered dataset using pandas aggregations."""
    if filtered_df.empty:
        return None

    most_dominant_idx = filtered_df["Pct_Gap"].idxmax()
    closest_title_idx = filtered_df["Pct_Gap"].idxmin()

    most_dominant = filtered_df.loc[most_dominant_idx]
    closest_title = filtered_df.loc[closest_title_idx]
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