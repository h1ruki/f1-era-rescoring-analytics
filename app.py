import os
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from db import (
    load_f1_data,
    SCORING_SYSTEMS,
    POINTS_REVISIONS,
    TEAM_COLORS,
)


st.set_page_config(
    page_title="F1 Championship Dominance Analyzer",
    page_icon="🏎️",
    layout="wide",
)

st.title("🏎️ F1 World Championship Dominance & What-If Engine")
st.markdown(
    "Analyze title victory margins, teammate gaps, and simulate historical title battles under alternate F1 point systems."
)


def get_contrast_text_color(hex_color):
    """Returns black for light background hex colors and white for dark ones."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return "#FFFFFF"
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    # Perceived luminance standard
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#0F172A" if luminance > 0.55 else "#FFFFFF"


# 1. Sidebar Controls & Session State Syncing
st.sidebar.header("Filter & What-If Simulation")

selected_scoring = st.sidebar.radio(
    "🧪 What-If Scoring Engine",
    list(SCORING_SYSTEMS.keys()),
    index=0,
    help="Recalculates historical points based on selected era rules!",
)

df_margins, top10_dict = load_f1_data(selected_scoring)

if df_margins.empty:
    st.warning("No data found or issue loading dataset.")
    st.stop()

ERAS = {
    "All Eras (1950-Present)": (1950, 2026),
    "V10 Era (1995-2005)": (1995, 2005),
    "V8 Era (2006-2013)": (2006, 2013),
    "Turbo-Hybrid Era (2014-2021)": (2014, 2021),
    "Ground Effect Era (2022-Present)": (2022, 2026),
    "Custom Range": None,
}

if "selected_era" not in st.session_state:
    st.session_state["selected_era"] = "All Eras (1950-Present)"
if "year_range" not in st.session_state:
    st.session_state["year_range"] = (1950, 2026)


def on_era_change():
    chosen_era = st.session_state["selected_era"]
    if chosen_era != "Custom Range" and ERAS[chosen_era] is not None:
        st.session_state["year_range"] = ERAS[chosen_era]


def on_slider_change():
    current_range = st.session_state["year_range"]
    matched_era = "Custom Range"
    for era_name, bounds in ERAS.items():
        if bounds == current_range:
            matched_era = era_name
            break
    st.session_state["selected_era"] = matched_era


st.sidebar.selectbox(
    "Select Technical Era",
    list(ERAS.keys()),
    key="selected_era",
    on_change=on_era_change,
)

st.sidebar.slider(
    "Select Year Range",
    int(df_margins["Season"].min()),
    int(df_margins["Season"].max()),
    key="year_range",
    on_change=on_slider_change,
)

show_points_lines = st.sidebar.checkbox("Highlight Points System Revisions", True)

year_range = st.session_state["year_range"]
filtered_df = (
    df_margins[
        (df_margins["Season"] >= year_range[0])
        & (df_margins["Season"] <= year_range[1])
    ]
    .sort_values("Season")
    .reset_index(drop=True)
)

# 2. Key Metrics
col1, col2, col3 = st.columns(3)

if not filtered_df.empty:
    most_dominant = filtered_df.loc[filtered_df["Pct_Gap"].idxmax()]
    closest_title = filtered_df.loc[filtered_df["Pct_Gap"].idxmin()]
    avg_gap = filtered_df["Pct_Gap"].mean()

    col1.metric(
        "Most Dominant Season",
        f"{most_dominant['Season']} ({most_dominant['Champion']})",
        f"{most_dominant['Pct_Gap']}% Gap",
    )
    col2.metric(
        "Closest Season",
        f"{closest_title['Season']} ({closest_title['Champion']})",
        f"{closest_title['Pct_Gap']}% Gap",
    )
    col3.metric("Avg Dominance Margin", f"{round(avg_gap, 1)}%")

# 3. Enhanced Interactive Plotly Chart
st.subheader(f"Title Victory Margin (%) — Mode: {selected_scoring}")

fig = go.Figure()

if not filtered_df.empty:
    for i in range(len(filtered_df) - 1):
        row_curr = filtered_df.iloc[i]
        row_next = filtered_df.iloc[i + 1]

        x_seg = [row_curr["Season"], row_next["Season"]]
        y_seg = [row_curr["Pct_Gap"], row_next["Pct_Gap"]]

        is_consecutive = (row_next["Season"] - row_curr["Season"]) == 1
        is_same_team = (
            row_curr["Champion_Team"] == row_next["Champion_Team"]
        ) and (row_curr["Champion_Team"] != "Unknown")
        is_same_driver = row_curr["Champion"] == row_next["Champion"]

        if is_consecutive and is_same_team:
            line_color = row_curr["Champion_Color"]

            if is_same_driver:
                fig.add_trace(
                    go.Scatter(
                        x=x_seg,
                        y=y_seg,
                        mode="lines",
                        line=dict(color=line_color, width=9),
                        opacity=0.18,
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=x_seg,
                        y=y_seg,
                        mode="lines",
                        line=dict(color=line_color, width=4, dash="solid"),
                        opacity=0.95,
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )
            else:
                fig.add_trace(
                    go.Scatter(
                        x=x_seg,
                        y=y_seg,
                        mode="lines",
                        line=dict(color="#4A5568", width=1.5, dash="solid"),
                        opacity=0.3,
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=x_seg,
                        y=y_seg,
                        mode="lines",
                        line=dict(color=line_color, width=4, dash="dot"),
                        opacity=0.9,
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )
        else:
            # Clear, visible transition lines across team shifts
            fig.add_trace(
                go.Scatter(
                    x=x_seg,
                    y=y_seg,
                    mode="lines",
                    line=dict(color="#64748B", width=1.8),
                    opacity=0.6,
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

    def get_initials(name):
        parts = name.strip().split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[-1][0]}".upper()
        return name[:2].upper()

    driver_initials = [get_initials(d) for d in filtered_df["Champion"]]
    text_colors = [
        get_contrast_text_color(c) for c in filtered_df["Champion_Color"]
    ]

    hover_texts = []
    for _, row in filtered_df.iterrows():
        season_yr = row["Season"]
        champ_team_html = f"<b style='color: {row['Champion_Color']};'>{row['Champion_Team']}</b>"
        runner_team_html = f"<b style='color: {row['RunnerUp_Color']};'>{row['RunnerUp_Team']}</b>"

        if row["Is_Teammate_Title_Fight"] == "Yes":
            tm_line = "⚔️ <b>Teammate Battle:</b> Runner-Up WAS teammate"
        else:
            tm_line = f"🤝 <b>Teammate Gap:</b> {row['Teammate_Gap_Info']}"

        pts_revision_note = ""
        if season_yr in POINTS_REVISIONS:
            pts_revision_note = f"<br>📌 <b>Points System:</b> <span style='color: #ECC94B;'>{POINTS_REVISIONS[season_yr]}</span>"

        if season_yr == 2026:
            top10_rows = top10_dict.get(2026, pd.DataFrame())
            top10_html_lines = []

            if not top10_rows.empty:
                for idx, t_row in top10_rows.iterrows():
                    t_team = t_row["Primary_Team"]
                    t_color = TEAM_COLORS.get(t_team, "#A0AEC0")
                    pos = int(t_row["Position"])
                    pts = t_row["TotalPoints"]
                    top10_html_lines.append(
                        f"P{pos:02d}. <b>{t_row['Driver']}</b> (<span style='color: {t_color};'>{t_team}</span>) — {pts:.0f} pts"
                    )

            top10_str = "<br>".join(top10_html_lines)

            hover_text = (
                f"<b>🏁 2026 Season (ONGOING)</b><br><br>"
                + f"👑 <b>Leader:</b> {row['Champion']} ({champ_team_html})<br>"
                + f"🥈 <b>P2 Chaser:</b> {row['RunnerUp']} ({runner_team_html})<br>"
                + f"📊 <b>Margin:</b> {row['Points_Gap']} pts ({row['Pct_Gap']}%)<br><br>"
                + f"<b>🏆 Current Top 10 Drivers:</b><br>{top10_str}"
            )
        else:
            hover_text = (
                f"<b>{season_yr} Season</b><br><br>"
                + f"🏎️ <b>Champion:</b> {row['Champion']} ({champ_team_html})<br>"
                + f"🏁 <b>Runner-Up:</b> {row['RunnerUp']} ({runner_team_html})<br>"
                + f"📊 <b>Title Gap:</b> {row['Points_Gap']} pts ({row['Pct_Gap']}%)<br>"
                + f"{tm_line}"
                + f"{pts_revision_note}"
            )

        hover_texts.append(hover_text)

    # Outer Halo Rings
    fig.add_trace(
        go.Scatter(
            x=filtered_df["Season"],
            y=filtered_df["Pct_Gap"],
            mode="markers",
            marker=dict(
                size=26,
                color=filtered_df["Champion_Color"],
                opacity=0.25,
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Larger Nodes with Dynamic High-Contrast Initials
    fig.add_trace(
        go.Scatter(
            x=filtered_df["Season"],
            y=filtered_df["Pct_Gap"],
            mode="markers+text",
            text=driver_initials,
            textposition="middle center",
            textfont=dict(
                size=9,
                color=text_colors,
                family="Arial Black",
            ),
            marker=dict(
                size=18,
                color=filtered_df["Champion_Color"],
                line=dict(width=1.8, color="#0F172A"),
            ),
            hovertext=hover_texts,
            hoverinfo="text",
            showlegend=False,
        )
    )

    avg_val = filtered_df["Pct_Gap"].mean()
    fig.add_hline(
        y=avg_val,
        line_dash="dash",
        line_color="#64748B",
        line_width=1.5,
        annotation_text=f"Era Mean Margin: {avg_val:.1f}%",
        annotation_position="bottom right",
        annotation_font=dict(color="#94A3B8", size=11),
    )

    if show_points_lines:
        for year, label in POINTS_REVISIONS.items():
            if year_range[0] <= year <= year_range[1]:
                fig.add_vline(
                    x=year,
                    line_dash="dot",
                    line_color="#E2E8F0",
                    line_width=1,
                    opacity=0.25,
                )

fig.update_layout(
    hovermode="x unified",
    height=580,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=20, t=30, b=20),
    xaxis=dict(
        showgrid=True,
        gridcolor="#1E293B",
        dtick=5 if len(filtered_df) > 15 else 1,
        tickfont=dict(color="#94A3B8"),
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor="#1E293B",
        title=dict(text="Title Victory Margin (%)", font=dict(color="#94A3B8")),
        tickfont=dict(color="#94A3B8"),
    ),
)

st.plotly_chart(fig, use_container_width=True)

# 4. Data Table View
with st.expander("View Raw Season Breakdown Table"):
    st.dataframe(filtered_df, use_container_width=True)