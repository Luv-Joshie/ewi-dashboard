"""
EWI Dashboard — Hyperinflation Early Warning System
=====================================================
Deployable version (Streamlit Community Cloud compatible).

Data source priority:
    1. A file uploaded via the sidebar uploader (works on any host, no Google Drive needed)
    2. A bundled file at DEFAULT_FILE_PATH sitting next to this script in the repo

Expected columns (case-insensitive match on "EWI"):
    date         → YYYY-MM-DD or YYYY-MM
    country      → country name
    <ewi col 1>  → logistic EWI score (0-100)
    <ewi col 2>  → PCA EWI score (0-100)  [optional]
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import os

# ── CONFIG ──────────────────────────────────────────────────────────────────
# If you bundle your data file in the same repo/folder as this script, put its
# name here so it loads automatically with no upload needed.
DEFAULT_FILE_PATH = "EWI_INDEX_ONLY_CONSERVATIVE.xlsx"

st.set_page_config(
    page_title="EWI Hyperinflation Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── COLORS ───────────────────────────────────────────────────────────────────
NAVY    = "#065A82"
TEAL    = "#028090"
SEAFOAM = "#02C39A"
LOW     = "#1D9E75"
MID     = "#EF9F27"
HIGH    = "#D85A30"
BG      = "#F4F7FA"
CARD_BG = "#FFFFFF"

# ── STYLES ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    [data-testid="stAppViewContainer"] {{ background-color: {BG}; }}
    [data-testid="stSidebar"] {{ background-color: {NAVY}; }}
    [data-testid="stSidebar"] * {{ color: white !important; }}
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stSlider label {{ color: #A8CCDC !important; font-size: 12px; }}
    .metric-card {{
        background: {CARD_BG};
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        border-left: 5px solid {TEAL};
        margin-bottom: 0.5rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }}
    .metric-label {{ font-size: 11px; color: #5A738A; font-weight: 600;
                     text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }}
    .metric-value {{ font-size: 32px; font-weight: 700; color: {NAVY}; line-height: 1; }}
    .metric-sub   {{ font-size: 12px; color: #5A738A; margin-top: 4px; }}
    .risk-badge {{
        display: inline-block; padding: 6px 18px; border-radius: 20px;
        font-weight: 700; font-size: 15px; letter-spacing: 0.04em;
    }}
    .risk-low  {{ background: #E1F5EE; color: #085041; }}
    .risk-mid  {{ background: #FAEEDA; color: #633806; }}
    .risk-high {{ background: #FAECE7; color: #712B13; }}
    .section-title {{
        font-size: 14px; font-weight: 600; color: {NAVY};
        text-transform: uppercase; letter-spacing: 0.06em;
        margin: 1.2rem 0 0.6rem;
    }}
    h1 {{ color: {NAVY} !important; }}
</style>
""", unsafe_allow_html=True)

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(file_obj_or_path):
    name = getattr(file_obj_or_path, "name", str(file_obj_or_path))
    if name.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_obj_or_path)
    else:
        df = pd.read_csv(file_obj_or_path)

    df.columns = df.columns.str.strip()
    cols = list(df.columns)
    ewi_cols = [c for c in cols if "ewi" in c.lower()]
    if len(ewi_cols) >= 2:
        df = df.rename(columns={ewi_cols[0]: "ewi_logistic", ewi_cols[1]: "ewi_pca"})
    elif len(ewi_cols) == 1:
        df = df.rename(columns={ewi_cols[0]: "ewi_logistic"})
        df["ewi_pca"] = np.nan
    else:
        st.error("Couldn't find any column with 'EWI' in its name. Check your file's headers.")
        st.stop()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.sort_values(["country", "date"])
    return df


with st.sidebar:
    st.markdown("## 📊 EWI Monitor")
    st.markdown(
        "<p style='color:#A8CCDC;font-size:12px;margin-top:-10px;'>Hyperinflation Early Warning</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

if not os.path.exists(DEFAULT_FILE_PATH):
    st.error(
        f"⚠️ Data file `{DEFAULT_FILE_PATH}` not found in the app folder. "
        "Make sure it's committed to the GitHub repo alongside ewi_dashboard.py."
    )
    st.stop()

try:
    df = load_data(DEFAULT_FILE_PATH)
except Exception as e:
    st.error(f"⚠️ Couldn't read the data file: {e}")
    st.stop()

# ── SIDEBAR CONTROLS ──────────────────────────────────────────────────────────
with st.sidebar:
    countries = sorted(df["country"].dropna().unique())
    selected_country = st.selectbox("Country", countries)

    min_date = df["date"].min().to_pydatetime()
    max_date = df["date"].max().to_pydatetime()
    date_range = st.slider(
        "Date Range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM",
    )

    show_pca = st.checkbox("Show PCA EWI", value=True)
    show_bands = st.checkbox("Show Risk Bands", value=True)

    st.markdown("---")
    st.markdown("<p style='color:#A8CCDC;font-size:11px;'>Risk Thresholds</p>", unsafe_allow_html=True)
    st.markdown("<p style='color:#02C39A;font-size:12px;'>● Low: 0–33</p>", unsafe_allow_html=True)
    st.markdown("<p style='color:#EF9F27;font-size:12px;'>● Moderate: 34–66</p>", unsafe_allow_html=True)
    st.markdown("<p style='color:#D85A30;font-size:12px;'>● High: 67–100</p>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        f"<p style='color:#A8CCDC;font-size:11px;'>Dataset: {len(df):,} observations<br>"
        f"{df['country'].nunique()} countries</p>",
        unsafe_allow_html=True,
    )

# ── FILTER DATA ───────────────────────────────────────────────────────────────
cdf = df[
    (df["country"] == selected_country)
    & (df["date"] >= pd.Timestamp(date_range[0]))
    & (df["date"] <= pd.Timestamp(date_range[1]))
].copy()

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("# Hyperinflation Early Warning Index")
st.markdown(
    f"<p style='color:#5A738A;margin-top:-12px;'>Real-time risk monitoring dashboard · {selected_country}</p>",
    unsafe_allow_html=True,
)

if cdf.empty:
    st.warning("No data for this selection.")
    st.stop()

# ── METRIC CARDS ──────────────────────────────────────────────────────────────
latest = cdf.iloc[-1]
ewi_now = latest.get("ewi_logistic", np.nan)
pca_now = latest.get("ewi_pca", np.nan)
prev = cdf.iloc[-2] if len(cdf) > 1 else latest
ewi_prev = prev.get("ewi_logistic", np.nan)
delta = ewi_now - ewi_prev if not np.isnan(ewi_prev) else 0


def risk_level(v):
    if np.isnan(v):
        return "N/A", "risk-low"
    if v < 34:
        return "LOW", "risk-low"
    if v < 67:
        return "MODERATE", "risk-mid"
    return "HIGH", "risk-high"


risk_label, risk_class = risk_level(ewi_now)
delta_str = f"{'▲' if delta >= 0 else '▼'} {abs(delta):.1f} vs prev month"
pca_now_str = f"{pca_now:.1f}" if not np.isnan(pca_now) else "N/A"

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Logistic EWI (Current)</div>
        <div class="metric-value">{ewi_now:.1f}</div>
        <div class="metric-sub">{delta_str}</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color:{SEAFOAM}">
        <div class="metric-label">PCA EWI (Current)</div>
        <div class="metric-value">{pca_now_str}</div>
        <div class="metric-sub">Unsupervised signal</div>
    </div>""", unsafe_allow_html=True)

with col3:
    max_ewi = cdf["ewi_logistic"].max()
    max_date_str = cdf.loc[cdf["ewi_logistic"].idxmax(), "date"].strftime("%b %Y")
    st.markdown(f"""
    <div class="metric-card" style="border-left-color:{HIGH}">
        <div class="metric-label">Historical Peak EWI</div>
        <div class="metric-value">{max_ewi:.1f}</div>
        <div class="metric-sub">Reached {max_date_str}</div>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color:{MID}">
        <div class="metric-label">Risk Classification</div>
        <div class="metric-value" style="font-size:22px;margin-top:4px;">
            <span class="risk-badge {risk_class}">{risk_label}</span>
        </div>
        <div class="metric-sub">Based on current logistic EWI</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── MAIN TIME SERIES CHART ────────────────────────────────────────────────────
st.markdown('<div class="section-title">EWI Over Time</div>', unsafe_allow_html=True)

fig = go.Figure()

if show_bands:
    for y0, y1, col, label in [
        (0, 33, "rgba(29,158,117,0.08)", "Low Risk"),
        (34, 66, "rgba(239,159,39,0.08)", "Moderate Risk"),
        (67, 100, "rgba(216,90,48,0.08)", "High Risk"),
    ]:
        fig.add_hrect(
            y0=y0, y1=y1, fillcolor=col, line_width=0, annotation_text=label,
            annotation_position="right", annotation_font_size=10,
            annotation_font_color="#5A738A",
        )

fig.add_trace(go.Scatter(
    x=cdf["date"], y=cdf["ewi_logistic"],
    name="Logistic EWI",
    line=dict(color=NAVY, width=2.5),
    fill="tozeroy",
    fillcolor="rgba(6,90,130,0.07)",
    hovertemplate="%{x|%b %Y}<br>Logistic EWI: <b>%{y:.1f}</b><extra></extra>",
))

if show_pca and "ewi_pca" in cdf.columns and not cdf["ewi_pca"].isna().all():
    fig.add_trace(go.Scatter(
        x=cdf["date"], y=cdf["ewi_pca"],
        name="PCA EWI",
        line=dict(color=SEAFOAM, width=2, dash="dot"),
        hovertemplate="%{x|%b %Y}<br>PCA EWI: <b>%{y:.1f}</b><extra></extra>",
    ))

fig.add_hline(y=67, line_dash="dot", line_color=HIGH, line_width=1,
              annotation_text="High threshold (67)", annotation_font_size=10)
fig.add_hline(y=34, line_dash="dot", line_color=MID, line_width=1,
              annotation_text="Moderate threshold (34)", annotation_font_size=10)

fig.update_layout(
    height=380,
    margin=dict(l=10, r=80, t=20, b=20),
    paper_bgcolor=CARD_BG,
    plot_bgcolor=CARD_BG,
    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
    xaxis=dict(showgrid=False, title=""),
    yaxis=dict(showgrid=True, gridcolor="#EEF2F6", title="EWI Score (0–100)", range=[0, 105]),
    font=dict(family="Calibri, sans-serif", color="#1A2B3C"),
    hovermode="x unified",
)
st.plotly_chart(fig, use_container_width=True)

# ── BOTTOM ROW ────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown('<div class="section-title">EWI Distribution</div>', unsafe_allow_html=True)
    fig2 = go.Figure()
    fig2.add_trace(go.Histogram(
        x=cdf["ewi_logistic"], nbinsx=30,
        marker_color=NAVY, opacity=0.8, name="Logistic EWI",
    ))
    if show_pca and not cdf["ewi_pca"].isna().all():
        fig2.add_trace(go.Histogram(
            x=cdf["ewi_pca"], nbinsx=30,
            marker_color=SEAFOAM, opacity=0.6, name="PCA EWI",
        ))
    for thresh, col in [(34, MID), (67, HIGH)]:
        fig2.add_vline(x=thresh, line_dash="dot", line_color=col, line_width=1.5)
    fig2.update_layout(
        height=280, barmode="overlay",
        margin=dict(l=10, r=10, t=10, b=30),
        paper_bgcolor=CARD_BG, plot_bgcolor=CARD_BG,
        xaxis=dict(showgrid=False, title="EWI Score"),
        yaxis=dict(showgrid=True, gridcolor="#EEF2F6", title="Months"),
        legend=dict(orientation="h", yanchor="bottom", y=1.0),
        font=dict(family="Calibri, sans-serif", color="#1A2B3C"),
    )
    st.plotly_chart(fig2, use_container_width=True)

with col_right:
    st.markdown('<div class="section-title">Cross-Country Snapshot (Latest)</div>', unsafe_allow_html=True)
    latest_all = df.sort_values("date").groupby("country").last().reset_index()
    latest_all = latest_all.dropna(subset=["ewi_logistic"]).sort_values("ewi_logistic", ascending=True).tail(20)

    def bar_color(v):
        if v < 34:
            return LOW
        if v < 67:
            return MID
        return HIGH

    colors = [bar_color(v) for v in latest_all["ewi_logistic"]]
    fig3 = go.Figure(go.Bar(
        x=latest_all["ewi_logistic"],
        y=latest_all["country"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:.1f}" for v in latest_all["ewi_logistic"]],
        textposition="outside",
        hovertemplate="%{y}: <b>%{x:.1f}</b><extra></extra>",
    ))
    if selected_country in latest_all["country"].values:
        idx = latest_all["country"].tolist().index(selected_country)
        colors[idx] = NAVY
        fig3.update_traces(marker_color=colors)

    fig3.update_layout(
        height=280,
        margin=dict(l=10, r=50, t=10, b=20),
        paper_bgcolor=CARD_BG, plot_bgcolor=CARD_BG,
        xaxis=dict(showgrid=True, gridcolor="#EEF2F6", title="", range=[0, 110]),
        yaxis=dict(showgrid=False, title=""),
        font=dict(family="Calibri, sans-serif", color="#1A2B3C", size=11),
    )
    st.plotly_chart(fig3, use_container_width=True)

# ── DATA TABLE ────────────────────────────────────────────────────────────────
with st.expander("📋 View Raw Data"):
    display_df = cdf[["date", "country", "ewi_logistic", "ewi_pca"]].copy()
    display_df["date"] = display_df["date"].dt.strftime("%Y-%m")
    display_df.columns = ["Date", "Country", "Logistic EWI", "PCA EWI"]
    display_df = display_df.sort_values("Date", ascending=False)
    st.dataframe(display_df, use_container_width=True, height=250)

st.markdown(
    "<br><p style='text-align:center;color:#5A738A;font-size:11px;'>"
    "EWI Hyperinflation Early Warning System · Hend Yousef, Dr. Dina Yousri & Prof. José Iparraguirre · GUC</p>",
    unsafe_allow_html=True,
)
