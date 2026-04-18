"""
Brain Drain Analysis App — Team 2: Economic Policy Advisors to the Governor
Upgraded v2.0: Multi-table ACS data with advanced metrics and visualizations.

VERIFIED CENSUS VARIABLE CODES (all validated against official Census API docs):
  B07009: Geographic Mobility by Educational Attainment (current residence)
    _001E  Total pop 25+
    _029E  Moved from different state: Bachelor's degree
    _030E  Moved from different state: Graduate or professional degree
    _025E  Moved from different state: Total (all education levels)

  B07409: Geographic Mobility by Educational Attainment (residence 1 year ago)
    _029E  Moved to different state: Bachelor's degree  (proxy for out-migration)
    _030E  Moved to different state: Graduate or professional degree
    _025E  Moved to different state: Total

  B15003: Educational Attainment for Pop 25+
    _001E  Total pop 25+
    _022E  Bachelor's degree holders (stock)
    _023E  Master's degree
    _024E  Professional school degree
    _025E  Doctorate degree

  B20004: Median Earnings by Sex by Educational Attainment (pop 25+)
    _001E  Total median earnings
    _005E  Bachelor's degree median earnings
    _006E  Graduate or professional degree median earnings
"""

import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from census import Census
import us

from services.gemini_service import (
    GroundingValidationError,
    answer_chat_question,
    explain_chart,
    generate_briefing,
)
from services.metric_context import (
    build_briefing_context,
    build_chart_context,
    route_chat_question,
)

#
# Page config
#
st.set_page_config(
    page_title="Brain Drain Intelligence Platform",
    layout="wide",
    initial_sidebar_state="expanded",
)

#
# CSS Styling
#
st.markdown("""
<style>
    :root {
        --app-bg: #0b1220;
        --surface: #111a2b;
        --surface-raised: #162238;
        --surface-soft: #1c2b45;
        --text-strong: #f8fafc;
        --text-body: #d9e2f2;
        --text-muted: #a8b6cc;
        --accent: #56b6ff;
        --accent-soft: rgba(86, 182, 255, 0.16);
        --positive: #27c281;
        --negative: #ef5350;
        --warning: #f6c453;
        --border: rgba(148, 163, 184, 0.24);
    }
    .stApp {
        background:
            radial-gradient(circle at top right, rgba(86, 182, 255, 0.08), transparent 28%),
            linear-gradient(180deg, #0a101a 0%, #0b1220 100%);
    }
    .metric-card {
        background: linear-gradient(180deg, var(--surface-soft) 0%, #24476f 100%);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.15rem 1.25rem;
        color: var(--text-strong);
        text-align: left;
        box-shadow: 0 12px 30px rgba(0,0,0,0.18);
    }
    .metric-card h2 { font-size: 2rem; margin: 0; font-weight: 750; color: var(--text-strong); letter-spacing: -0.02em; }
    .metric-card p  { font-size: 0.92rem; margin: 0.45rem 0 0; color: var(--text-strong); font-weight: 600; }
    .metric-card .metric-desc { font-size: 0.8rem; margin-top: 0.55rem; color: var(--text-body); line-height: 1.35; }
    .metric-card .metric-formula { font-size: 0.72rem; margin-top: 0.45rem; color: var(--text-muted); line-height: 1.25; }
    .policy-box {
        background: linear-gradient(180deg, rgba(17, 26, 43, 0.96) 0%, rgba(13, 21, 34, 0.96) 100%);
        border: 1px solid var(--border);
        border-left: 5px solid var(--accent);
        border-radius: 14px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        color: var(--text-strong);
        box-shadow: 0 8px 24px rgba(0,0,0,0.16);
    }
    .policy-box h4 { color: var(--text-strong); margin-top: 0; }
    .policy-box p, .policy-box li, .policy-box ul { color: var(--text-body); }
    .policy-box b { color: var(--accent); }
    .warn-box {
        background: linear-gradient(180deg, rgba(38, 28, 8, 0.96) 0%, rgba(26, 18, 0, 0.96) 100%);
        border: 1px solid rgba(246, 196, 83, 0.26);
        border-left: 5px solid var(--warning);
        border-radius: 14px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        color: var(--text-strong);
    }
    .warn-box h4 { color: #ffe082; margin-top: 0; }
    .warn-box p, .warn-box li { color: #fff7e6; }
    .warn-box b { color: #fff7e6; }
    .section-header {
        margin: 1.9rem 0 1rem;
        padding-bottom: 0.8rem;
        border-bottom: 1px solid rgba(86, 182, 255, 0.35);
    }
    .section-header h3 {
        margin: 0;
        color: var(--text-strong);
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .section-header p {
        margin: 0.35rem 0 0;
        color: var(--text-body);
        font-size: 0.88rem;
        line-height: 1.4;
    }
    .context-banner {
        background: linear-gradient(180deg, rgba(17, 26, 43, 0.96) 0%, rgba(13, 21, 34, 0.96) 100%);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 0.95rem 1.1rem;
        margin: 0.8rem 0 1.4rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.14);
    }
    .context-banner .context-title {
        color: var(--text-strong);
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.55rem;
    }
    .context-banner .context-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .context-banner .pill {
        display: inline-flex;
        align-items: center;
        padding: 0.38rem 0.7rem;
        border-radius: 999px;
        background: var(--accent-soft);
        border: 1px solid rgba(86, 182, 255, 0.18);
        color: var(--text-body);
        font-size: 0.8rem;
    }
    .context-banner .pill strong {
        color: var(--text-strong);
        margin-right: 0.35rem;
    }
    .helper-note {
        background: rgba(86, 182, 255, 0.08);
        border: 1px solid rgba(86, 182, 255, 0.18);
        border-radius: 12px;
        padding: 0.7rem 0.85rem;
        color: var(--text-body);
        font-size: 0.86rem;
        margin: 0.5rem 0 1rem;
    }
    .ai-panel {
        background: linear-gradient(180deg, rgba(16, 28, 47, 0.95) 0%, rgba(10, 18, 32, 0.95) 100%);
        border: 1px solid rgba(86, 182, 255, 0.24);
        border-radius: 16px;
        padding: 0.9rem 1rem;
        margin-top: 0.75rem;
    }
    .ai-panel h4 {
        margin: 0 0 0.5rem 0;
        color: var(--text-strong);
    }
    .ai-meta {
        color: var(--text-muted);
        font-size: 0.76rem;
        margin-top: 0.65rem;
    }
    .summary-stat {
        background: rgba(255,255,255,0.02);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 0.85rem 0.95rem;
        height: 100%;
    }
    .summary-stat .label {
        color: var(--text-muted);
        font-size: 0.8rem;
        margin-bottom: 0.3rem;
    }
    .summary-stat .value {
        color: var(--text-strong);
        font-size: 1.4rem;
        font-weight: 700;
    }
    [data-testid="stMetricValue"] {
        color: var(--text-strong);
    }
    [data-testid="stMetricLabel"] {
        color: var(--text-body);
    }
</style>
""", unsafe_allow_html=True)

#
# API Key
#
API_KEY = st.secrets["CENSUS_API_KEY"]
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
AI_AVAILABLE = bool(GEMINI_API_KEY)

#
# DATA LOADING FUNCTIONS (modular, cached)
#

#
# DATA LOADING
#

def _census_to_df(raw_data, col_map):
    """Convert Census API response (list of dicts) to a clean DataFrame."""
    rows = []
    for record in raw_data:
        row = {}
        for src_key, dst_key in col_map.items():
            row[dst_key] = record.get(src_key)
        rows.append(row)
    return pd.DataFrame(rows)


@st.cache_data(show_spinner="Loading in-migration data (B07009)...")
def load_b07009():
    c = Census(API_KEY)
    data = c.acs5.state(
        ("NAME", "B07009_001E", "B07009_025E", "B07009_029E", "B07009_030E"),
        Census.ALL
    )
    df = _census_to_df(data, {
        "NAME":         "state",
        "B07009_001E":  "pop_25plus",
        "B07009_025E":  "interstate_in_total",
        "B07009_029E":  "interstate_in_bachelors",
        "B07009_030E":  "interstate_in_graduate",
    })
    num_cols = ["pop_25plus", "interstate_in_total", "interstate_in_bachelors", "interstate_in_graduate"]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    df["interstate_in_educated"] = df["interstate_in_bachelors"] + df["interstate_in_graduate"]
    return df.dropna(subset=["pop_25plus"])


@st.cache_data(show_spinner="Loading out-migration proxy data (B07409)...")
def load_b07409():
    c = Census(API_KEY)
    data = c.acs5.state(
        ("NAME", "B07409_025E", "B07409_029E", "B07409_030E"),
        Census.ALL
    )
    df = _census_to_df(data, {
        "NAME":         "state",
        "B07409_025E":  "interstate_out_total",
        "B07409_029E":  "interstate_out_bachelors",
        "B07409_030E":  "interstate_out_graduate",
    })
    num_cols = ["interstate_out_total", "interstate_out_bachelors", "interstate_out_graduate"]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    df["interstate_out_educated"] = df["interstate_out_bachelors"] + df["interstate_out_graduate"]
    return df


@st.cache_data(show_spinner="Loading education stock data (B15003)...")
def load_b15003():
    c = Census(API_KEY)
    data = c.acs5.state(
        ("NAME", "B15003_001E", "B15003_022E", "B15003_023E", "B15003_024E", "B15003_025E"),
        Census.ALL
    )
    df = _census_to_df(data, {
        "NAME":         "state",
        "B15003_001E":  "educ_pop_total",
        "B15003_022E":  "stock_bachelors",
        "B15003_023E":  "stock_masters",
        "B15003_024E":  "stock_professional",
        "B15003_025E":  "stock_doctorate",
    })
    num_cols = ["educ_pop_total", "stock_bachelors", "stock_masters", "stock_professional", "stock_doctorate"]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    df["stock_graduate_plus"]  = df["stock_masters"] + df["stock_professional"] + df["stock_doctorate"]
    df["stock_educated_total"] = df["stock_bachelors"] + df["stock_graduate_plus"]
    return df


@st.cache_data(show_spinner="Loading earnings data (B20004)...")
def load_b20004():
    c = Census(API_KEY)
    data = c.acs5.state(
        ("NAME", "B20004_001E", "B20004_005E", "B20004_006E"),
        Census.ALL
    )
    df = _census_to_df(data, {
        "NAME":         "state",
        "B20004_001E":  "median_earnings_total",
        "B20004_005E":  "median_earnings_bachelors",
        "B20004_006E":  "median_earnings_graduate",
    })
    num_cols = ["median_earnings_total", "median_earnings_bachelors", "median_earnings_graduate"]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    return df


@st.cache_data(show_spinner="Loading young interstate in-migration data (B07001)...")
def load_b07001_young():
    c = Census(API_KEY)
    data = c.acs5.state(
        ("NAME", "B07001_006E", "B07001_007E", "B07001_070E", "B07001_071E"),
        Census.ALL
    )
    df = _census_to_df(data, {
        "NAME": "state",
        "B07001_006E": "pop_25_29",
        "B07001_007E": "pop_30_34",
        "B07001_070E": "young_in_25_29",
        "B07001_071E": "young_in_30_34",
    })
    num_cols = ["pop_25_29", "pop_30_34", "young_in_25_29", "young_in_30_34"]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    df["young_pop_25_34"] = df["pop_25_29"] + df["pop_30_34"]
    df["young_interstate_in"] = df["young_in_25_29"] + df["young_in_30_34"]
    return df


@st.cache_data(show_spinner="Loading young interstate out-migration proxy data (B07401)...")
def load_b07401_young():
    c = Census(API_KEY)
    data = c.acs5.state(
        ("NAME", "B07401_070E", "B07401_071E"),
        Census.ALL
    )
    df = _census_to_df(data, {
        "NAME": "state",
        "B07401_070E": "young_out_25_29",
        "B07401_071E": "young_out_30_34",
    })
    num_cols = ["young_out_25_29", "young_out_30_34"]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    df["young_interstate_out"] = df["young_out_25_29"] + df["young_out_30_34"]
    return df


@st.cache_data(show_spinner="Loading affordability pressure data (B25070)...")
def load_b25070():
    c = Census(API_KEY)
    data = c.acs5.state(
        ("NAME", "B25070_001E", "B25070_007E", "B25070_008E", "B25070_009E", "B25070_010E", "B25070_011E"),
        Census.ALL
    )
    df = _census_to_df(data, {
        "NAME": "state",
        "B25070_001E": "renter_households_total",
        "B25070_007E": "rent_30_34",
        "B25070_008E": "rent_35_39",
        "B25070_009E": "rent_40_49",
        "B25070_010E": "rent_50_plus",
        "B25070_011E": "rent_not_computed",
    })
    num_cols = [
        "renter_households_total",
        "rent_30_34",
        "rent_35_39",
        "rent_40_49",
        "rent_50_plus",
        "rent_not_computed",
    ]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    df["rent_burdened_30plus"] = df["rent_30_34"] + df["rent_35_39"] + df["rent_40_49"] + df["rent_50_plus"]
    df["renter_households_computed"] = df["renter_households_total"] - df["rent_not_computed"]
    df["rent_burden_30plus_rate"] = (
        df["rent_burdened_30plus"] / df["renter_households_computed"].replace(0, pd.NA)
    ) * 100
    return df


@st.cache_data(show_spinner="Assembling master dataset…")
def load_master():
    """
    Joins all four tables and computes advanced policy metrics.
    """
    b7 = load_b07009()
    b7_out = load_b07409()
    b15 = load_b15003()
    b20 = load_b20004()
    b07001_young = load_b07001_young()
    b07401_young = load_b07401_young()
    b25070 = load_b25070()

    df = b7.merge(b7_out, on="state", how="left")
    df = df.merge(b15, on="state", how="left")
    df = df.merge(b20, on="state", how="left")
    df = df.merge(b07001_young, on="state", how="left")
    df = df.merge(b07401_young, on="state", how="left")
    df = df.merge(b25070, on="state", how="left")

    #  Core migration metrics
    # Rate: educated in-migrants per 1,000 residents 25+
    df["edu_inmig_rate"] = (df["interstate_in_educated"] / df["pop_25plus"]) * 1_000

    # Rate: educated out-migrants per 1,000 residents 25+
    df["edu_outmig_rate"] = (df["interstate_out_educated"] / df["pop_25plus"]) * 1_000

    # Net educated migration (gain = positive, loss = negative)
    df["net_educated_migrants"] = df["interstate_in_educated"] - df["interstate_out_educated"]
    df["net_migration_rate"] = df["edu_inmig_rate"] - df["edu_outmig_rate"]

    #  Education stock metrics
    # Educated migrants as % of total educated stock
    df["inmig_pct_of_stock"] = (df["interstate_in_educated"] / df["stock_educated_total"]) * 100
    df["outmig_pct_of_stock"] = (df["interstate_out_educated"] / df["stock_educated_total"]) * 100

    # Educated migration as % of total interstate migration
    df["edu_share_of_inmig"] = (df["interstate_in_educated"] / df["interstate_in_total"].replace(0, pd.NA)) * 100
    df["edu_share_of_outmig"] = (df["interstate_out_educated"] / df["interstate_out_total"].replace(0, pd.NA)) * 100

    #  Talent concentration index
    # % of state's adult population that holds a bachelor's degree or higher
    df["talent_concentration"] = (df["stock_educated_total"] / df["educ_pop_total"]) * 100

    #  Earnings premium
    df["bachelors_earnings_premium"] = df["median_earnings_bachelors"] - df["median_earnings_total"]
    df["graduate_earnings_premium"] = df["median_earnings_graduate"] - df["median_earnings_total"]

    # Young talent mobility (ages 25-34)
    df["young_net_migrants"] = df["young_interstate_in"] - df["young_interstate_out"]
    df["young_inmig_rate"] = (df["young_interstate_in"] / df["young_pop_25_34"].replace(0, pd.NA)) * 1_000
    df["young_outmig_rate"] = (df["young_interstate_out"] / df["young_pop_25_34"].replace(0, pd.NA)) * 1_000
    df["young_net_migration_rate"] = df["young_inmig_rate"] - df["young_outmig_rate"]

    #  Policy labels
    nat_median_rate = df["net_migration_rate"].median()
    nat_median_conc = df["talent_concentration"].median()

    def segment(row):
        high_net = row["net_migration_rate"] > nat_median_rate
        high_conc = row["talent_concentration"] > nat_median_conc
        if high_net and high_conc:
            return "Talent Hub"
        elif high_net and not high_conc:
            return "Rising Gainer"
        elif not high_net and high_conc:
            return "At-Risk Retainer"
        else:
            return "Brain Drain Risk"

    df["segment"] = df.apply(segment, axis=1)

    return df.dropna(subset=["pop_25plus", "stock_educated_total"])


#
# LOAD DATA
#
df = load_master()

#
# SIDEBAR
#
with st.sidebar:
    st.markdown("##  Brain Drain Intelligence")
    st.caption("ACS 5-Year Estimates | Team 2 Policy Analysis")
    st.divider()

    analysis_section = st.radio(
        "**Analysis Module**",
        [
            " Executive Dashboard",
            " Young Talent + Affordability Risk",
            " State Comparison Tool",
            " Governor's Briefing",
            " Methodology & Limitations",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    # Global state selector
    all_states = sorted(df["state"].dropna().unique())
    state_filter_options = ["All States"] + all_states
    selected_state = st.selectbox(" State Filter", state_filter_options, index=0)
    focal_state = selected_state if selected_state != "All States" else None

    if analysis_section == " Executive Dashboard":
        st.markdown("### Visual Filters")
        selected_segments = st.multiselect(
            "Policy Segments",
            options=sorted(df["segment"].dropna().unique()),
            default=sorted(df["segment"].dropna().unique()),
        )
        selected_visual_states = st.multiselect(
            "States in Visuals",
            options=all_states,
            default=[],
            placeholder="Leave empty to show all states",
        )
        migration_direction = st.selectbox(
            "Migration Direction Filter",
            ["All States", "Net Gainers", "Net Losers"],
            index=0,
        )
        dashboard_focus = st.selectbox(
            "Executive Dashboard Focus",
            ["Educated migrants", "Young migrants"],
            index=0,
        )
        st.caption("Metric mode: normalized per 1k")
    else:
        selected_segments = sorted(df["segment"].dropna().unique())
        selected_visual_states = []
        migration_direction = "All States"
        dashboard_focus = "Educated migrants"


#
# HELPER: metric card HTML
#
def metric_card(value, label, description=None, formula=None):
    description_html = f'<div class="metric-desc">{description}</div>' if description else ""
    formula_html = f'<div class="metric-formula">{formula}</div>' if formula else ""
    return f"""<div class="metric-card"><h2>{value}</h2><p>{label}</p>{description_html}{formula_html}</div>"""


def render_section_header(title, helper_text=None):
    helper_html = f"<p>{helper_text}</p>" if helper_text else ""
    st.markdown(
        f'<div class="section-header"><h3>{title}</h3>{helper_html}</div>',
        unsafe_allow_html=True,
    )


def render_context_banner(title, items):
    pills = "".join(
        f'<span class="pill"><strong>{label}:</strong> {value}</span>'
        for label, value in items
    )
    st.markdown(
        (
            '<div class="context-banner">'
            f'<div class="context-title">{title}</div>'
            f'<div class="context-row">{pills}</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


def render_helper_note(text):
    st.markdown(f'<div class="helper-note">{text}</div>', unsafe_allow_html=True)


def render_ai_panel_start(title):
    st.markdown(f'<div class="ai-panel"><h4>{title}</h4>', unsafe_allow_html=True)


def render_ai_panel_end(meta_lines=None):
    if meta_lines:
        for line in meta_lines:
            st.markdown(f'<div class="ai-meta">{line}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def classify_consistency(row):
    if row["net_migration_rate"] >= 0 and row["young_net_migration_rate"] < 0:
        return "Educated Positive / Young Negative"
    if row["net_migration_rate"] >= 0 and row["young_net_migration_rate"] >= 0:
        return "Educated Positive / Young Positive"
    if row["net_migration_rate"] < 0 and row["young_net_migration_rate"] >= 0:
        return "Educated Negative / Young Positive"
    return "Educated Negative / Young Negative"


def format_metric_value(value, is_currency=False):
    if pd.isna(value):
        return "N/A"
    if is_currency:
        return f"${value:,.0f}"
    if isinstance(value, str):
        return value
    if abs(value) >= 100:
        return f"{value:+,.0f}" if value < 0 else f"{value:,.0f}"
    return f"{value:+.2f}" if value < 0 else f"{value:.2f}"


def hsl_color(hue, saturation=78, lightness=58, alpha=None):
    if alpha is None:
        return f"hsl({hue}, {saturation}%, {lightness}%)"
    return f"hsla({hue}, {saturation}%, {lightness}%, {alpha})"


def get_signal_hsl(signal):
    palette = {
        "positive": hsl_color(190, 80, 60),
        "warning": hsl_color(38, 84, 62),
        "negative": hsl_color(10, 82, 60),
        "neutral": hsl_color(220, 18, 72),
    }
    return palette.get(signal, palette["neutral"])


def score_metric_against_median(value, median, lower_is_better=False, tolerance=0.02):
    if pd.isna(value) or pd.isna(median):
        return "neutral"
    scale = max(abs(median), 1.0)
    if lower_is_better:
        if value < median - (scale * tolerance):
            return "positive"
        if value > median + (scale * tolerance):
            return "negative"
        return "warning"
    if value > median + (scale * tolerance):
        return "positive"
    if value < median - (scale * tolerance):
        return "negative"
    return "warning"


def _table_styles():
    return [
        {
            "selector": "th",
            "props": [
                ("background-color", "#171c26"),
                ("color", "#e9eef8"),
                ("font-weight", "700"),
                ("border", "1px solid rgba(255,255,255,0.08)"),
                ("padding", "0.65rem 0.8rem"),
            ],
        },
        {
            "selector": "td",
            "props": [
                ("background-color", "#0f141c"),
                ("color", "#eef4ff"),
                ("border", "1px solid rgba(255,255,255,0.06)"),
                ("padding", "0.55rem 0.8rem"),
            ],
        },
        {
            "selector": "table",
            "props": [
                ("border-collapse", "collapse"),
                ("border-radius", "12px"),
                ("overflow", "hidden"),
            ],
        },
    ]


def _blend_channel(start, end, ratio):
    return round(start + (end - start) * ratio)


def _hsl_scale_css(value, series, lower_is_better=False):
    if pd.isna(value):
        return "background-color: rgba(255,255,255,0.02); color: #eef4ff;"
    finite = series.dropna()
    if finite.empty:
        return "background-color: rgba(255,255,255,0.02); color: #eef4ff;"
    mn, mx = float(finite.min()), float(finite.max())
    ratio = 0.5 if mx == mn else (float(value) - mn) / (mx - mn)
    if lower_is_better:
        ratio = 1 - ratio
    hue = _blend_channel(10, 150, ratio)
    sat = _blend_channel(78, 56, ratio)
    light = _blend_channel(56, 34, ratio)
    text_color = "#081018" if ratio >= 0.58 else "#f8fbff"
    return f"background-color: {hsl_color(hue, sat, light)}; color: {text_color}; font-weight: 650;"


def _rent_burden_hsl_css(value, series):
    if pd.isna(value):
        return "background-color: rgba(255,255,255,0.02); color: #eef4ff;"
    finite = series.dropna()
    if finite.empty:
        return "background-color: rgba(255,255,255,0.02); color: #eef4ff;"
    mn, mx = float(finite.min()), float(finite.max())
    ratio = 0.5 if mx == mn else (float(value) - mn) / (mx - mn)
    # Lower rent burden is better: low values read greener, high values redder.
    hue = _blend_channel(150, 8, ratio)
    sat = _blend_channel(52, 82, ratio)
    light = _blend_channel(34, 58, ratio)
    text_color = "#081018" if ratio <= 0.22 else "#f8fbff"
    return f"background-color: {hsl_color(hue, sat, light)}; color: {text_color}; font-weight: 700;"


def style_young_diagnostic_table(diag_df):
    styler = (
        diag_df.style
        .format({
            "Young In-Migrants": "{:,.0f}",
            "Young Out-Migrants (est.)": "{:,.0f}",
            "Young Net Migrants": "{:+,.0f}",
            "Young In-Rate (per 1k)": "{:.2f}",
            "Young Out-Rate (per 1k)": "{:.2f}",
            "Young Net Rate (per 1k)": "{:+.2f}",
            "Rent Burden Rate 30%+": "{:.1f}%",
        })
        .set_table_styles(_table_styles())
    )
    styler = styler.map(
        lambda value: _hsl_scale_css(value, diag_df["Young Net Rate (per 1k)"], lower_is_better=False),
        subset=["Young Net Rate (per 1k)"],
    )
    styler = styler.map(
        lambda value: _rent_burden_hsl_css(value, diag_df["Rent Burden Rate 30%+"]),
        subset=["Rent Burden Rate 30%+"],
    )
    styler = styler.map(lambda _: "color: #f8fbff; font-weight: 600;", subset=["State"])
    return styler


def get_metric_mode_config(dashboard_focus="Educated migrants"):
    is_young_focus = dashboard_focus == "Young migrants"
    primary_metric_col = "young_net_migration_rate" if is_young_focus else "net_migration_rate"
    primary_metric_label = "Young Net Rate (25-34, per 1k)" if is_young_focus else "Educated Net Rate (per 1k)"
    primary_metric_axis = "Young Net Migration Rate (per 1k, ages 25-34)" if is_young_focus else "Educated Net Migration Rate (per 1k)"
    comparison_metric_col = "talent_concentration" if is_young_focus else "young_net_migration_rate"
    comparison_metric_label = "Talent Concentration (%)" if is_young_focus else "Young Net Rate (25-34, per 1k)"
    return {
        "normalized": True,
        "dashboard_focus": dashboard_focus,
        "is_young_focus": is_young_focus,
        "metric_col": primary_metric_col,
        "metric_label": primary_metric_label,
        "metric_axis": primary_metric_axis,
        "metric_title_prefix": "Young" if is_young_focus else "Educated",
        "in_count_col": "young_interstate_in" if is_young_focus else "interstate_in_educated",
        "out_count_col": "young_interstate_out" if is_young_focus else "interstate_out_educated",
        "net_count_col": "young_net_migrants" if is_young_focus else "net_educated_migrants",
        "in_count_label": "Young In-Migrants (25-34)" if is_young_focus else "Educated In-Migrants",
        "out_count_label": "Young Out-Migrants (25-34, est.)" if is_young_focus else "Educated Out-Migrants (est.)",
        "net_count_label": "Young Net Migration" if is_young_focus else "Net Educated Migration",
        "comparison_metric_col": comparison_metric_col,
        "comparison_metric_label": comparison_metric_label,
        "young_col": "young_net_migration_rate",
        "young_label": "Young Net Rate (25-34, per 1k)",
        "young_axis": "Young Net Migration Rate (per 1k, ages 25-34)",
        "educated_col": "net_migration_rate",
        "educated_label": "Educated Net Rate (per 1k)",
        "educated_axis": "Educated Net Migration Rate (per 1k)",
        "mode_suffix": "Rate",
    }


def filter_states_by_direction(df_src, direction, metric_col):
    if direction == "Net Gainers":
        return df_src[df_src[metric_col] >= 0]
    if direction == "Net Losers":
        return df_src[df_src[metric_col] < 0]
    return df_src


def build_visual_filter_context(selected_segments, selected_visual_states, migration_direction):
    return {
        "policy_segments": selected_segments,
        "states_in_visuals": selected_visual_states if selected_visual_states else "All States",
        "educated_migration_filter": migration_direction,
    }


def merge_visual_states(selected_visual_states, focal_state):
    merged_states = list(selected_visual_states)
    if merged_states and focal_state and focal_state not in merged_states:
        merged_states.append(focal_state)
    return merged_states


def build_executive_filtered_df(df_src, selected_segments, selected_visual_states, migration_direction, metric_col):
    filtered_df = df_src[df_src["segment"].isin(selected_segments)].copy()
    if selected_visual_states:
        filtered_df = filtered_df[filtered_df["state"].isin(selected_visual_states)]
    return filter_states_by_direction(filtered_df, migration_direction, metric_col)


def get_effective_focal_state_for_visuals(focal_state, selected_visual_states):
    if focal_state is None:
        return None
    if not selected_visual_states:
        return focal_state
    return focal_state if focal_state in selected_visual_states else None


def build_color_encoding_context(chart_id, focal_state=None):
    if chart_id == "quadrant":
        return {
            "color_channel": "policy segment categories",
            "palette": {
                "Talent Hub": "#1565c0",
                "Rising Gainer": "#2e7d32",
                "At-Risk Retainer": "#f57c00",
                "Brain Drain Risk": "#c62828",
            },
            "purpose": "Separates policy segments so users can compare state position and segment at the same time.",
            "highlight": f"{focal_state} is highlighted in gold." if focal_state else "No single state highlight is applied.",
        }
    if chart_id == "choropleth":
        return {
            "color_channel": "educated net migration rate on a diverging red-blue scale",
            "palette": {
                "negative_values": "red",
                "positive_values": "blue",
                "zero_center": "neutral midpoint",
            },
            "purpose": "Makes gains and losses easy to distinguish geographically around a zero baseline.",
            "highlight": f"{focal_state} is outlined in gold." if focal_state else "No single state outline is applied.",
        }
    if chart_id == "peer_gaps":
        return {
            "color_channel": "metric type",
            "purpose": "Separates the three benchmark gaps so each state can be compared across measures without mixing bars together.",
        }
    if chart_id == "housing_young":
        return {
            "color_channel": "young migration sign",
            "palette": {
                "Positive": "#1565c0",
                "Negative": "#c62828",
            },
            "purpose": "Makes it easy to distinguish states gaining young adults from states losing them.",
            "highlight": f"{focal_state} is highlighted in gold." if focal_state else "No single state highlight is applied.",
        }
    if chart_id == "earnings_net":
        return {
            "color_channel": "educated net migration sign",
            "palette": {
                "Positive": "#1565c0",
                "Negative": "#c62828",
            },
            "purpose": "Separates net gainers from net losers while showing how earnings align with migration performance.",
            "highlight": f"{focal_state} is highlighted in gold." if focal_state else "No single state highlight is applied.",
        }
    return {}


def ai_caption():
    render_helper_note("AI output is grounded only in Census-derived dashboard metrics and the methodology notes in this app.")


def get_briefing_cache_key(state):
    return f"ai_briefing::{state}"


def get_chart_cache_key(chart_id, state):
    return f"chart_explainer::{chart_id}::{state}"


def get_chat_state_key(page_key):
    return f"chat_messages::{page_key}"


def render_chart_fallback(chart_context):
    focal_state = chart_context.get("focal_state") or "the current filtered view"
    if "focal_point" in chart_context:
        focal_metrics = ", ".join(
            f"{label.replace('_', ' ')}: {value}"
            for label, value in chart_context["focal_point"].items()
        )
    else:
        focal_metrics = f"value: {chart_context.get('focal_value', 'N/A')}"
    st.info(
        f"{chart_context['chart_title']} for {focal_state}. "
        f"Focal state metrics from the dashboard are {focal_metrics}. "
        "Use the chart tooltips and methodology notes for the exact underlying values."
    )


def build_deterministic_briefing_payload(df, focal_state):
    focal = df[df["state"] == focal_state].iloc[0]
    ranked_net = df["net_migration_rate"].rank(ascending=False, method="min")
    ranked_young = df["young_net_migration_rate"].rank(ascending=False, method="min")
    ranked_rent = df["rent_burden_30plus_rate"].rank(ascending=True, method="min")
    state_count = int(df["state"].nunique())

    strengths = []
    risks = []
    policy_options = []

    if focal["net_migration_rate"] >= df["net_migration_rate"].median():
        strengths.append(
            f"{focal_state} is above the national median on educated net migration at {focal['net_migration_rate']:+.2f} per 1,000."
        )
    else:
        risks.append(
            f"{focal_state} is below the national median on educated net migration at {focal['net_migration_rate']:+.2f} per 1,000."
        )

    if focal["young_net_migration_rate"] >= 0:
        strengths.append(
            f"Young adult migration is positive at {focal['young_net_migration_rate']:+.2f} per 1,000, suggesting the state is retaining or attracting ages 25 to 34."
        )
    else:
        risks.append(
            f"Young adult migration is negative at {focal['young_net_migration_rate']:+.2f} per 1,000, which points to pressure in the early-career pipeline."
        )

    if focal["rent_burden_30plus_rate"] > df["rent_burden_30plus_rate"].median():
        risks.append(
            f"Rent burden is {focal['rent_burden_30plus_rate']:.1f}%, above the national median, which may weaken talent attraction."
        )
        policy_options.append("Explore renter affordability and housing supply measures in high-pressure markets.")
    else:
        strengths.append(
            f"Rent burden is {focal['rent_burden_30plus_rate']:.1f}%, below the national median, which is a relative affordability advantage."
        )

    if focal["bachelors_earnings_premium"] >= df["bachelors_earnings_premium"].median():
        strengths.append(
            f"The bachelor's earnings premium is ${focal['bachelors_earnings_premium']:,.0f}, above the national median."
        )
        policy_options.append("Use wage competitiveness as part of employer recruitment and retention strategy.")
    else:
        risks.append(
            f"The bachelor's earnings premium is ${focal['bachelors_earnings_premium']:,.0f}, below the national median."
        )
        policy_options.append("Examine whether wage competitiveness is limiting educated worker attraction.")

    if not policy_options:
        policy_options.append("Track the same metrics over time and compare against peer states before targeting intervention.")

    executive_summary = (
        f"{focal_state} sits in the {focal['segment']} segment with educated net migration of "
        f"{focal['net_migration_rate']:+.2f} per 1,000 and talent concentration of {focal['talent_concentration']:.1f}%. "
        f"It ranks {int(ranked_net.loc[focal.name])} of {state_count} on educated net migration, "
        f"{int(ranked_young.loc[focal.name])} of {state_count} on young net migration, and "
        f"{int(ranked_rent.loc[focal.name])} of {state_count} on rent burden where lower is better."
    )

    return {
        "headline": f"{focal_state}: Deterministic Governor Briefing",
        "executive_summary": executive_summary,
        "strengths": strengths,
        "risks": risks,
        "policy_options": policy_options,
    }


def build_briefing_visual_df(df, focal_state):
    focal = df[df["state"] == focal_state].iloc[0]
    metrics = [
        {
            "label": "Educated Net Rate",
            "column": "net_migration_rate",
            "value": float(focal["net_migration_rate"]),
            "display": f"{focal['net_migration_rate']:+.2f} per 1k",
            "median": float(df["net_migration_rate"].median()),
            "lower_is_better": False,
        },
        {
            "label": "Young Net Rate",
            "column": "young_net_migration_rate",
            "value": float(focal["young_net_migration_rate"]),
            "display": f"{focal['young_net_migration_rate']:+.2f} per 1k",
            "median": float(df["young_net_migration_rate"].median()),
            "lower_is_better": False,
        },
        {
            "label": "Talent Concentration",
            "column": "talent_concentration",
            "value": float(focal["talent_concentration"]),
            "display": f"{focal['talent_concentration']:.1f}%",
            "median": float(df["talent_concentration"].median()),
            "lower_is_better": False,
        },
        {
            "label": "Rent Burden",
            "column": "rent_burden_30plus_rate",
            "value": float(focal["rent_burden_30plus_rate"]),
            "display": f"{focal['rent_burden_30plus_rate']:.1f}%",
            "median": float(df["rent_burden_30plus_rate"].median()),
            "lower_is_better": True,
        },
        {
            "label": "BA Earnings Premium",
            "column": "bachelors_earnings_premium",
            "value": float(focal["bachelors_earnings_premium"]),
            "display": f"${focal['bachelors_earnings_premium']:,.0f}",
            "median": float(df["bachelors_earnings_premium"].median()),
            "lower_is_better": False,
        },
    ]
    rows = []
    for item in metrics:
        series = df[item["column"]].rank(pct=True)
        percentile = float(series.loc[focal.name] * 100)
        if item["lower_is_better"]:
            percentile = 100 - percentile
        signal = score_metric_against_median(
            item["value"],
            item["median"],
            lower_is_better=item["lower_is_better"],
            tolerance=0.02,
        )
        rows.append(
            {
                "Metric": item["label"],
                "Display": item["display"],
                "Signal": signal,
                "Color": get_signal_hsl(signal),
                "PercentileScore": percentile,
                "MedianScore": 50,
                "MedianValue": item["median"],
                "MedianDisplay": f"U.S. median: {item['median']:.1f}" if item["label"] not in {"BA Earnings Premium", "Educated Net Rate", "Young Net Rate"} else (
                    f"U.S. median: ${item['median']:,.0f}" if item["label"] == "BA Earnings Premium" else f"U.S. median: {item['median']:+.2f} per 1k"
                ),
                "BetterWhen": "Lower is better" if item["lower_is_better"] else "Higher is better",
            }
        )
    return pd.DataFrame(rows), str(focal["segment"])


def render_briefing_payload(payload, deterministic=False):
    if deterministic:
        st.caption("Rendered from dashboard metrics because AI briefing generation was unavailable.")
    if "headline" in payload:
        st.subheader(payload["headline"])
        st.write(payload["executive_summary"])
        if payload.get("strengths"):
            st.markdown("**Strengths**")
            for item in payload["strengths"]:
                st.write(f"- {item}")
        if payload.get("risks"):
            st.markdown("**Risks**")
            for item in payload["risks"]:
                st.write(f"- {item}")
        if payload.get("policy_options"):
            st.markdown("**Policy Options to Explore**")
            for item in payload["policy_options"]:
                st.write(f"- {item}")


def summarize_chart_data_used(chart_context):
    filter_bits = []
    applied_filters = chart_context.get("applied_filters", {})
    if applied_filters:
        for label, value in applied_filters.items():
            if isinstance(value, list):
                value_text = ", ".join(value) if value else "All"
            else:
                value_text = str(value)
            filter_bits.append(f"{label.replace('_', ' ').title()}: {value_text}")
    if chart_context.get("chart_id") == "peer_gaps":
        peers = chart_context.get("peer_states", [])
        if peers:
            peer_text = f"Selected peer benchmarking states: {', '.join(peers)}"
            if filter_bits:
                return peer_text + " | " + " | ".join(filter_bits)
            return peer_text
    if filter_bits:
        return " | ".join(filter_bits)
    return "Chart summary for the current dashboard view"


def summarize_data_used(tool_name, tool_payload):
    if tool_name == "get_national_summary":
        return [
            "National medians for net migration, young migration, talent concentration, rent burden, and BA earnings premium",
            "Top and bottom state lists across migration, rent burden, and talent concentration",
            "Policy segment counts across all states",
        ]
    if tool_name == "get_full_dashboard_context":
        return [
            "All states in the dashboard-wide Census-derived dataset",
            "National medians and leaderboards across major metrics",
            "State-level rows for migration, talent concentration, rent burden, earnings, and segment",
        ]
    if tool_name == "get_state_metrics":
        state = tool_payload.get("state", "selected state")
        return [f"Dashboard metrics for {state}"]
    if tool_name == "compare_states":
        states = tool_payload.get("states", [])
        if len(states) == 2:
            return [f"Dashboard comparison for {states[0]} and {states[1]}"]
    if tool_name == "analyze_metric_relationship":
        return [
            f"{tool_payload.get('metric_a_label', 'Metric A')} and {tool_payload.get('metric_b_label', 'Metric B')}",
            "All-state rows where both metrics are available",
            "Cross-state relationship summary for the two metrics",
        ]
    if tool_name == "rank_states":
        metric = tool_payload.get("metric", "selected metric")
        return [f"Top ranked states for {metric}"]
    if tool_name == "find_peer_states":
        state = tool_payload.get("state", "selected state")
        return [f"Nearest peer-state matches for {state}"]
    if tool_name == "get_chart_summary":
        return ["Chart-specific summary for the current dashboard visual"]
    if tool_name == "get_methodology_notes":
        return ["Methodology notes and interpretation limits from the dashboard"]
    return ["Dashboard-derived tool result"]


def render_chat_block(page_key, page_title, df, focal_state, all_states, peer_states=None):
    render_section_header(page_title, "Ask focused questions about the metrics currently in scope.")
    ai_caption()

    if not AI_AVAILABLE:
        st.info("Add `GEMINI_API_KEY` to `.streamlit/secrets.toml` to enable grounded AI answers.")
        return

    chat_key = get_chat_state_key(page_key)
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    with st.container(border=True):
        with st.form(f"{page_key}_chat_form", clear_on_submit=True):
            question = st.text_input(
                "Ask a question about the dashboard data",
                placeholder="Example: What does the overall national dataset show about brain drain and rent burden?",
            )
            submitted = st.form_submit_button("Ask")

    clear_clicked = st.button("Clear chat", key=f"{page_key}_clear_chat")
    if clear_clicked:
        st.session_state[chat_key] = []

    if submitted and question.strip():
        route = route_chat_question(
            df,
            question.strip(),
            focal_state,
            all_states,
            peer_states=peer_states,
        )
        try:
            response = answer_chat_question(
                GEMINI_API_KEY,
                question.strip(),
                route["tool_payload"],
            )
            st.session_state[chat_key].append(
                {
                    "question": question.strip(),
                    "answer": response.answer,
                    "data_used": summarize_data_used(route["tool_name"], route["tool_payload"]),
                    "tool_name": route["tool_name"],
                }
            )
        except GroundingValidationError:
            st.session_state[chat_key].append(
                {
                    "question": question.strip(),
                    "answer": "I could not produce a fully grounded answer for that request. Please try a narrower question tied to the displayed metrics or comparisons.",
                    "data_used": [],
                    "tool_name": route["tool_name"],
                }
            )
        except Exception as exc:
            st.session_state[chat_key].append(
                {
                    "question": question.strip(),
                    "answer": f"The AI assistant is temporarily unavailable: {exc}",
                    "data_used": [],
                    "tool_name": route["tool_name"],
                }
            )

    for item in reversed(st.session_state[chat_key]):
        with st.container(border=True):
            st.markdown(f"**You:** {item['question']}")
            st.markdown(f"**Assistant:** {item['answer']}")
            if item["data_used"]:
                st.caption("Data used: " + " | ".join(item["data_used"]))
            st.caption(f"Tool path: `{item['tool_name']}`")


#
# MODULE 1: EXECUTIVE DASHBOARD
#
if analysis_section == " Executive Dashboard":
    st.title("Brain Drain Intelligence Platform")
    st.markdown("**Team 2 — Economic Policy Advisors to the Governor** | ACS 5-Year Estimates")

    mode_config = get_metric_mode_config(dashboard_focus)
    focal = df[df["state"] == focal_state].iloc[0] if focal_state else None
    visual_states_for_charts = merge_visual_states(selected_visual_states, focal_state)
    visual_filter_context = build_visual_filter_context(
        selected_segments,
        visual_states_for_charts,
        migration_direction,
    )
    filtered_df = build_executive_filtered_df(
        df,
        selected_segments,
        visual_states_for_charts,
        migration_direction,
        mode_config["metric_col"],
    )
    effective_focal_state_for_visuals = get_effective_focal_state_for_visuals(
        focal_state,
        visual_states_for_charts,
    )
    visual_focal = (
        filtered_df[filtered_df["state"] == effective_focal_state_for_visuals].iloc[0]
        if effective_focal_state_for_visuals and effective_focal_state_for_visuals in filtered_df["state"].values
        else None
    )
    visuals_available = not filtered_df.empty

    render_section_header("Overview")

    # KPI Row
    if focal is not None:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.markdown(metric_card(
                f"{int(focal[mode_config['in_count_col']]):,}",
                mode_config["in_count_label"],
                "People in the selected migration cohort who moved into the state.",
                "cohort in-migrants",
            ), unsafe_allow_html=True)
        with col2:
            st.markdown(metric_card(
                f"{int(focal[mode_config['out_count_col']]):,}",
                mode_config["out_count_label"],
                "People in the selected migration cohort estimated to have moved out.",
                "cohort out-migrants",
            ), unsafe_allow_html=True)
        with col3:
            net = int(focal[mode_config["net_count_col"]])
            color = "#2e7d32" if net >= 0 else "#c62828"
            st.markdown(f"""<div class="metric-card" style="background: linear-gradient(135deg, {color} 0%, {'#43a047' if net>=0 else '#e53935'} 100%);">
                <h2>{net:+,}</h2><p>{mode_config['net_count_label']}</p>
                <div class="metric-desc">The balance between arrivals and departures in the selected migration cohort.</div>
                <div class="metric-formula">in-migrants - out-migrants</div></div>""", unsafe_allow_html=True)
        with col4:
            st.markdown(metric_card(
                f"{focal['talent_concentration']:.1f}%",
                "Talent Concentration",
                "Share of adults who already hold at least a bachelor's degree.",
                "educated stock / adults 25+ x 100",
            ), unsafe_allow_html=True)
        with col5:
            st.markdown(metric_card(
                focal["segment"],
                "Policy Segment",
                "A quick label showing the state's migration and talent position.",
                "based on net migration rate + talent concentration",
            ), unsafe_allow_html=True)
    else:
        top_row = st.columns(3, gap="large")
        with top_row[0]:
            st.markdown(metric_card(
                f"{int(filtered_df[mode_config['in_count_col']].sum()):,}",
                mode_config["in_count_label"],
                "Sum across all states currently included in the dashboard filters.",
                "sum across filtered states",
            ), unsafe_allow_html=True)
        with top_row[1]:
            st.markdown(metric_card(
                f"{int(filtered_df[mode_config['out_count_col']].sum()):,}",
                mode_config["out_count_label"],
                "Sum across all states currently included in the dashboard filters.",
                "sum across filtered states",
            ), unsafe_allow_html=True)
        with top_row[2]:
            st.markdown(metric_card(
                f"{filtered_df['talent_concentration'].median():.1f}%" if visuals_available else "N/A",
                "Median Talent Concentration",
                "Median share of adults with at least a bachelor's degree.",
                "educated stock / adults 25+ x 100",
            ), unsafe_allow_html=True)
        st.markdown("<div style='height: 0.9rem;'></div>", unsafe_allow_html=True)
        bottom_row = st.columns(3, gap="large")
        with bottom_row[0]:
            st.markdown(metric_card(
                format_metric_value(filtered_df[mode_config["metric_col"]].median()) if visuals_available else "N/A",
                f"Median {mode_config['metric_label']}",
                "Median migration balance across the current filtered view.",
                "median selected-cohort net rate",
            ), unsafe_allow_html=True)
        with bottom_row[1]:
            st.markdown(metric_card(
                f"{filtered_df['rent_burden_30plus_rate'].median():.1f}%" if visuals_available else "N/A",
                "Median Rent Burden",
                "Median share of renters spending at least 30% of income on housing.",
                "rent-burdened renters / renter households x 100",
            ), unsafe_allow_html=True)
        with bottom_row[2]:
            st.markdown(metric_card(
                f"${filtered_df['bachelors_earnings_premium'].median():,.0f}" if visuals_available else "N/A",
                "Median BA Earnings Premium",
                "Median earnings advantage for bachelor's degree holders.",
                "BA median earnings - overall median earnings",
            ), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Decision scorecard for presentation
    if focal is not None:
        s1, s2, s3, s4 = st.columns(4)
        scorecard_source = focal
        with s1:
            st.markdown(metric_card(
                format_metric_value(scorecard_source[mode_config["metric_col"]]),
                mode_config["metric_label"],
                "Net gain or loss in the selected migration cohort after adjusting for cohort size.",
                "selected-cohort in rate - out rate",
            ), unsafe_allow_html=True)
        with s2:
            st.markdown(metric_card(
                f"{scorecard_source['talent_concentration']:.1f}%",
                "Talent Concentration",
                "Share of adults with at least a bachelor's degree.",
                "educated stock / adults 25+ x 100",
            ), unsafe_allow_html=True)
        with s3:
            st.markdown(metric_card(
                f"{scorecard_source['rent_burden_30plus_rate']:.1f}%",
                "Rent Burden (30%+)",
                "Share of renters spending at least 30% of income on housing.",
                "rent-burdened renters / renter households x 100",
            ), unsafe_allow_html=True)
        with s4:
            st.markdown(metric_card(
                f"${scorecard_source['bachelors_earnings_premium']:,.0f}",
                "BA Earnings Premium",
                "How much more bachelor's degree holders earn than the average worker.",
                "BA median earnings - overall median earnings",
            ), unsafe_allow_html=True)

    if focal is not None and not mode_config["is_young_focus"] and focal["net_migration_rate"] >= 0 and focal["young_net_migration_rate"] < 0:
        st.markdown("""
        <div class="warn-box">
        <b>Signal Divergence:</b> Educated net migration is positive, but young (25-34) net migration is negative.
        This is a direct comparison of two ACS-derived metrics.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if not visuals_available:
        st.warning("No states match the current visual filters. Charts now stay empty until the filters intersect again.")
    else:
        render_section_header("Positioning")
        color_map = {
            "Talent Hub": "#1565c0",
            "Rising Gainer": "#2e7d32",
            "At-Risk Retainer": "#f57c00",
            "Brain Drain Risk": "#c62828",
        }

        fig_quad = px.scatter(
            filtered_df,
            x=mode_config["metric_col"],
            y="talent_concentration",
            size="stock_educated_total",
            color="segment",
            color_discrete_map=color_map,
            hover_name="state",
            hover_data={
                mode_config["metric_col"]: ":.2f" if mode_config["normalized"] else ":,",
                "talent_concentration": ":.1f",
                mode_config["net_count_col"]: ":,",
                "stock_educated_total": ":,",
                "segment": False,
            },
            labels={
                mode_config["metric_col"]: mode_config["metric_axis"],
                "talent_concentration": "Talent Concentration (%)",
                "stock_educated_total": "Total Educated Stock",
            },
            title=f"State Talent Positioning: {mode_config['metric_label']} vs. Talent Concentration",
            height=520,
        )
        fig_quad.add_hline(y=filtered_df["talent_concentration"].median(), line_dash="dash", line_color="gray", opacity=0.5)
        fig_quad.add_vline(x=filtered_df[mode_config["metric_col"]].median(), line_dash="dash", line_color="gray", opacity=0.5)
        if visual_focal is not None:
            fig_quad.add_scatter(
                x=[visual_focal[mode_config["metric_col"]]],
                y=[visual_focal["talent_concentration"]],
                mode="markers+text",
                text=[effective_focal_state_for_visuals],
                textposition="top right",
                marker=dict(size=18, color="gold", line=dict(width=2, color="black")),
                showlegend=False,
                name=effective_focal_state_for_visuals,
            )
        fig_quad.update_layout(legend_title="Policy Segment")
        st.plotly_chart(fig_quad, use_container_width=True)
        if AI_AVAILABLE:
            quadrant_key = get_chart_cache_key("quadrant", effective_focal_state_for_visuals or "none")
            quadrant_context = build_chart_context(
                filtered_df,
                "quadrant",
                effective_focal_state_for_visuals,
                applied_filters=visual_filter_context,
                visual_encoding=build_color_encoding_context("quadrant", effective_focal_state_for_visuals),
            )
            if st.button("Explain this chart", key=f"{quadrant_key}_button"):
                try:
                    st.session_state[quadrant_key] = explain_chart(GEMINI_API_KEY, quadrant_context).model_dump()
                except GroundingValidationError:
                    st.session_state[quadrant_key] = {"fallback": quadrant_context}
                except Exception as exc:
                    st.session_state[quadrant_key] = {"error": str(exc), "fallback": quadrant_context}
            if quadrant_key in st.session_state:
                with st.container(border=True):
                    render_section_header("AI chart explanation")
                    ai_caption()
                    payload = st.session_state[quadrant_key]
                    if "paragraph" in payload:
                        st.write(payload["paragraph"])
                        st.caption("Data used: " + summarize_chart_data_used(quadrant_context))
                        st.caption("Tool path: `get_chart_summary`")
                    else:
                        if payload.get("error"):
                            st.caption(f"AI unavailable: {payload['error']}")
                        render_chart_fallback(payload["fallback"])

        render_section_header("Geographic Brain Drain Signal")
        map_df = filtered_df[["state", mode_config["metric_col"], "segment", "talent_concentration", mode_config["net_count_col"]]].copy()
        map_df["id"] = map_df["state"].apply(lambda s: us.states.lookup(s).fips if us.states.lookup(s) else None)
        map_df = map_df.dropna(subset=["id", mode_config["metric_col"]])
        map_df["id"] = map_df["id"].astype(str).str.zfill(2)
        max_abs_rate = float(map_df[mode_config["metric_col"]].abs().max()) if not map_df.empty else 1.0
        if max_abs_rate == 0:
            max_abs_rate = 1.0

        states_topo = alt.topo_feature("https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json", "states")
        base_states = (
            alt.Chart(states_topo)
            .mark_geoshape(fill="#e5e7eb", stroke="#9ca3af", strokeWidth=0.8)
            .project(type="albersUsa")
            .properties(height=500)
        )
        choropleth = (
            alt.Chart(states_topo)
            .mark_geoshape(stroke="#374151", strokeWidth=0.4)
            .transform_calculate(
                id_str="toString(datum.id).length == 1 ? '0' + toString(datum.id) : toString(datum.id)"
            )
            .transform_lookup(
                lookup="id_str",
                from_=alt.LookupData(
                    map_df,
                    "id",
                    ["state", mode_config["metric_col"], "segment", "talent_concentration", mode_config["net_count_col"]],
                ),
            )
            .encode(
                color=alt.Color(
                    f"{mode_config['metric_col']}:Q",
                    title=mode_config["metric_label"],
                    scale=alt.Scale(scheme="redblue", domain=[-max_abs_rate, max_abs_rate]),
                ),
                tooltip=[
                    alt.Tooltip("state:N", title="State"),
                    alt.Tooltip(f"{mode_config['metric_col']}:Q", title=mode_config["metric_label"], format=".2f" if mode_config["normalized"] else ",.0f"),
                    alt.Tooltip(f"{mode_config['net_count_col']}:Q", title=mode_config["net_count_label"], format=",.0f"),
                    alt.Tooltip("talent_concentration:Q", title="Talent Concentration (%)", format=".1f"),
                    alt.Tooltip("segment:N", title="Segment"),
                ],
            )
            .project(type="albersUsa")
            .properties(height=500)
        )

        map_layers = [base_states, choropleth]
        if effective_focal_state_for_visuals is not None:
            focal_outline = (
                alt.Chart(states_topo)
                .mark_geoshape(fillOpacity=0, stroke="#f9a825", strokeWidth=2.5)
                .transform_calculate(
                    id_str="toString(datum.id).length == 1 ? '0' + toString(datum.id) : toString(datum.id)"
                )
                .transform_lookup(
                    lookup="id_str",
                    from_=alt.LookupData(map_df, "id", ["state"]),
                )
                .transform_filter(alt.datum.state == effective_focal_state_for_visuals)
                .project(type="albersUsa")
            )
            map_layers.append(focal_outline)

        st.altair_chart(alt.layer(*map_layers), use_container_width=True)
        if AI_AVAILABLE:
            choropleth_key = get_chart_cache_key("choropleth", effective_focal_state_for_visuals or "none")
            choropleth_context = build_chart_context(
                map_df,
                "choropleth",
                effective_focal_state_for_visuals,
                applied_filters=visual_filter_context,
                visual_encoding=build_color_encoding_context("choropleth", effective_focal_state_for_visuals),
            )
            if st.button("Explain this chart", key=f"{choropleth_key}_button"):
                try:
                    st.session_state[choropleth_key] = explain_chart(GEMINI_API_KEY, choropleth_context).model_dump()
                except GroundingValidationError:
                    st.session_state[choropleth_key] = {"fallback": choropleth_context}
                except Exception as exc:
                    st.session_state[choropleth_key] = {"error": str(exc), "fallback": choropleth_context}
            if choropleth_key in st.session_state:
                with st.container(border=True):
                    render_section_header("AI chart explanation")
                    ai_caption()
                    payload = st.session_state[choropleth_key]
                    if "paragraph" in payload:
                        st.write(payload["paragraph"])
                        st.caption("Data used: " + summarize_chart_data_used(choropleth_context))
                        st.caption("Tool path: `get_chart_summary`")
                    else:
                        if payload.get("error"):
                            st.caption(f"AI unavailable: {payload['error']}")
                        render_chart_fallback(payload["fallback"])

    # Peer benchmarking
    render_section_header("Peer Benchmarking")
    selected_peers = []
    if focal is not None:
        selected_peers = st.multiselect(
            "Peer States",
            options=[s for s in all_states if s != focal_state],
            default=[],
            max_selections=5,
        )
        benchmark_states = [focal_state] + selected_peers
        bench = df[df["state"].isin(benchmark_states)].copy()

        rank_primary = df[mode_config["metric_col"]].rank(ascending=False, method="min")
        rank_secondary = df[mode_config["comparison_metric_col"]].rank(ascending=False, method="min")
        rank_rent = df["rent_burden_30plus_rate"].rank(ascending=True, method="min")
        rank_premium = df["bachelors_earnings_premium"].rank(ascending=False, method="min")
        national_medians = {
            mode_config["metric_col"]: df[mode_config["metric_col"]].median(),
            mode_config["comparison_metric_col"]: df[mode_config["comparison_metric_col"]].median(),
            "rent_burden_30plus_rate": df["rent_burden_30plus_rate"].median(),
            "bachelors_earnings_premium": df["bachelors_earnings_premium"].median(),
        }

        bench["Rank Primary"] = bench.index.map(rank_primary)
        bench["Rank Secondary"] = bench.index.map(rank_secondary)
        bench["Rank Rent"] = bench.index.map(rank_rent)
        bench["Rank Premium"] = bench.index.map(rank_premium)
        bench["Gap vs US Median (Primary)"] = bench[mode_config["metric_col"]] - national_medians[mode_config["metric_col"]]
        bench["Gap vs US Median (Secondary)"] = bench[mode_config["comparison_metric_col"]] - national_medians[mode_config["comparison_metric_col"]]
        bench["Gap vs US Median (Rent)"] = bench["rent_burden_30plus_rate"] - national_medians["rent_burden_30plus_rate"]
        bench["Gap vs US Median (Premium)"] = bench["bachelors_earnings_premium"] - national_medians["bachelors_earnings_premium"]

        benchmark_table = bench[
            [
                "state",
                mode_config["metric_col"],
                mode_config["comparison_metric_col"],
                "rent_burden_30plus_rate",
                "bachelors_earnings_premium",
                "Rank Primary",
                "Rank Secondary",
                "Rank Rent",
                "Rank Premium",
                "Gap vs US Median (Primary)",
                "Gap vs US Median (Secondary)",
                "Gap vs US Median (Rent)",
                "Gap vs US Median (Premium)",
            ]
        ].copy()
        benchmark_table.columns = [
            "State",
            mode_config["metric_label"],
            mode_config["comparison_metric_label"],
            "Rent Burden (30%+)",
            "BA Earnings Premium ($)",
            f"Rank: {mode_config['metric_title_prefix']}",
            f"Rank: {mode_config['comparison_metric_label']}",
            "Rank: Rent (lower better)",
            "Rank: Premium",
            f"Gap to US Median: {mode_config['metric_label']}",
            f"Gap to US Median: {mode_config['comparison_metric_label']}",
            "Gap to US Median: Rent",
            "Gap to US Median: Premium",
        ]
        st.dataframe(benchmark_table.round(2), use_container_width=True, hide_index=True)

        gap_chart = bench[["state", "Gap vs US Median (Primary)", "Gap vs US Median (Secondary)", "Gap vs US Median (Rent)"]].melt(
            id_vars="state",
            var_name="Metric",
            value_name="Gap",
        )
        gap_chart["Metric"] = gap_chart["Metric"].map({
            "Gap vs US Median (Primary)": f"{mode_config['metric_label']} Gap",
            "Gap vs US Median (Secondary)": f"{mode_config['comparison_metric_label']} Gap",
            "Gap vs US Median (Rent)": "Rent Burden Gap",
        })
        fig_gap = px.bar(
            gap_chart,
            x="state",
            y="Gap",
            color="Metric",
            barmode="group",
            title=f"Peer Gaps vs U.S. Median ({mode_config['mode_suffix']} View)",
            height=420,
        )
        fig_gap.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_gap, use_container_width=True)
        if AI_AVAILABLE:
            peer_gap_key = get_chart_cache_key("peer_gaps", focal_state)
            peer_gap_context = build_chart_context(
                bench,
                "peer_gaps",
                focal_state,
                peer_states=selected_peers,
                applied_filters={"peer_states": benchmark_states},
                benchmark_df=df,
                visual_encoding=build_color_encoding_context("peer_gaps", focal_state),
            )
            if st.button("Explain this chart", key=f"{peer_gap_key}_button"):
                try:
                    st.session_state[peer_gap_key] = explain_chart(GEMINI_API_KEY, peer_gap_context).model_dump()
                except GroundingValidationError:
                    st.session_state[peer_gap_key] = {"fallback": peer_gap_context}
                except Exception as exc:
                    st.session_state[peer_gap_key] = {"error": str(exc), "fallback": peer_gap_context}
            if peer_gap_key in st.session_state:
                with st.expander("AI Chart Explanation", expanded=True):
                    ai_caption()
                    payload = st.session_state[peer_gap_key]
                    if "paragraph" in payload:
                        st.write(payload["paragraph"])
                        st.caption("Data used: " + summarize_chart_data_used(peer_gap_context))
                        st.caption("Tool path: `get_chart_summary`")
                    else:
                        if payload.get("error"):
                            st.caption(f"AI unavailable: {payload['error']}")
                        render_chart_fallback(payload["fallback"])
    else:
        st.info("Choose a state in the sidebar if you want to run peer benchmarking against specific comparison states.")

    render_section_header("Potential Brain Drain Drivers")
    left_col, right_col = st.columns(2)

    with left_col:
        if visuals_available:
            df_young_exec = filtered_df.dropna(subset=[mode_config["young_col"], "rent_burden_30plus_rate", "young_pop_25_34"]).copy()
            df_young_exec["young_flow_sign"] = df_young_exec[mode_config["young_col"]].apply(lambda v: "Positive" if v >= 0 else "Negative")
            fig_young_housing_exec = px.scatter(
                df_young_exec,
                x="rent_burden_30plus_rate",
                y=mode_config["young_col"],
                color="young_flow_sign",
                size="young_pop_25_34",
                hover_name="state",
                color_discrete_map={"Positive": "#1565c0", "Negative": "#c62828"},
                labels={
                    "rent_burden_30plus_rate": "Renter Cost-Burden Rate (30%+)",
                    mode_config["young_col"]: mode_config["young_axis"],
                    "young_flow_sign": "Young Net Sign",
                },
                title="Housing Pressure vs. Young Net Migration",
                height=520,
            )
            fig_young_housing_exec.add_hline(y=0, line_dash="dash", line_color="gray")
            fig_young_housing_exec.add_vline(
                x=df_young_exec["rent_burden_30plus_rate"].median(),
                line_dash="dash",
                line_color="gray",
            )
            if visual_focal is not None:
                fig_young_housing_exec.add_scatter(
                    x=[visual_focal["rent_burden_30plus_rate"]],
                    y=[visual_focal[mode_config["young_col"]]],
                    mode="markers+text",
                    text=[effective_focal_state_for_visuals],
                    textposition="top right",
                    marker=dict(size=16, color="gold", line=dict(width=2, color="black")),
                    showlegend=False,
                )
            fig_young_housing_exec.update_layout(showlegend=True)
            st.plotly_chart(fig_young_housing_exec, use_container_width=True)
            st.caption("Positive means the state gained young adults ages 25-34; negative means it lost them.")
            if AI_AVAILABLE:
                housing_key = get_chart_cache_key("housing_young", effective_focal_state_for_visuals or "none")
                housing_context = build_chart_context(
                    df_young_exec,
                    "housing_young",
                    effective_focal_state_for_visuals,
                    applied_filters={
                        **visual_filter_context,
                        "chart_scope": "states with non-null housing and young migration values",
                    },
                    visual_encoding=build_color_encoding_context("housing_young", effective_focal_state_for_visuals),
                )
                if st.button("Explain this chart", key=f"{housing_key}_button"):
                    try:
                        st.session_state[housing_key] = explain_chart(GEMINI_API_KEY, housing_context).model_dump()
                    except GroundingValidationError:
                        st.session_state[housing_key] = {"fallback": housing_context}
                    except Exception as exc:
                        st.session_state[housing_key] = {"error": str(exc), "fallback": housing_context}
                if housing_key in st.session_state:
                    with st.expander("AI Chart Explanation", expanded=True):
                        ai_caption()
                        payload = st.session_state[housing_key]
                        if "paragraph" in payload:
                            st.write(payload["paragraph"])
                            st.caption("Data used: " + summarize_chart_data_used(housing_context))
                            st.caption("Tool path: `get_chart_summary`")
                        else:
                            if payload.get("error"):
                                st.caption(f"AI unavailable: {payload['error']}")
                            render_chart_fallback(payload["fallback"])
        else:
            st.info("Housing-pressure chart is waiting for a visual-filter combination that returns at least one state.")

    with right_col:
        if visuals_available:
            df_earn = filtered_df.dropna(subset=["median_earnings_bachelors", "net_migration_rate"]).copy()
            df_earn["net_flow_sign"] = df_earn["net_migration_rate"].apply(lambda v: "Positive" if v >= 0 else "Negative")
            fig_earn = px.scatter(
                df_earn,
                x="median_earnings_bachelors",
                y="net_migration_rate",
                size="stock_educated_total",
                color="net_flow_sign",
                hover_name="state",
                color_discrete_map={"Positive": "#1565c0", "Negative": "#c62828"},
                labels={
                    "median_earnings_bachelors": "Median Earnings: Bachelor's Degree ($)",
                    "net_migration_rate": "Net Educated Migration Rate (per 1k)",
                    "net_flow_sign": "Net Flow Sign",
                },
                title="Bachelor's Earnings vs. Net Migration",
                height=520,
            )
            fig_earn.add_hline(y=0, line_dash="dash", line_color="gray")
            fig_earn.add_vline(
                x=df_earn["median_earnings_bachelors"].median(),
                line_dash="dash",
                line_color="gray",
            )
            if visual_focal is not None:
                fig_earn.add_scatter(
                    x=[visual_focal["median_earnings_bachelors"]],
                    y=[visual_focal["net_migration_rate"]],
                    mode="markers+text",
                    text=[effective_focal_state_for_visuals],
                    textposition="top right",
                    marker=dict(size=16, color="gold", line=dict(width=2, color="black")),
                    showlegend=False,
                )
            fig_earn.update_layout(showlegend=True)
            st.plotly_chart(fig_earn, use_container_width=True)
            st.caption("Positive means the state gained educated people overall; negative means it lost them.")
            if AI_AVAILABLE:
                earnings_key = get_chart_cache_key("earnings_net", effective_focal_state_for_visuals or "none")
                earnings_context = build_chart_context(
                    df_earn,
                    "earnings_net",
                    effective_focal_state_for_visuals,
                    applied_filters={
                        **visual_filter_context,
                        "chart_scope": "states with non-null earnings and net migration values",
                    },
                    visual_encoding=build_color_encoding_context("earnings_net", effective_focal_state_for_visuals),
                )
                if st.button("Explain this chart", key=f"{earnings_key}_button"):
                    try:
                        st.session_state[earnings_key] = explain_chart(GEMINI_API_KEY, earnings_context).model_dump()
                    except GroundingValidationError:
                        st.session_state[earnings_key] = {"fallback": earnings_context}
                    except Exception as exc:
                        st.session_state[earnings_key] = {"error": str(exc), "fallback": earnings_context}
                if earnings_key in st.session_state:
                    with st.expander("AI Chart Explanation", expanded=True):
                        ai_caption()
                        payload = st.session_state[earnings_key]
                        if "paragraph" in payload:
                            st.write(payload["paragraph"])
                            st.caption("Data used: " + summarize_chart_data_used(earnings_context))
                            st.caption("Tool path: `get_chart_summary`")
                        else:
                            if payload.get("error"):
                                st.caption(f"AI unavailable: {payload['error']}")
                            render_chart_fallback(payload["fallback"])
        else:
            st.info("Earnings chart is waiting for a visual-filter combination that returns at least one state.")

#
# MODULE 5: STATE COMPARISON
#
elif analysis_section == " Young Talent + Affordability Risk":
    st.header(" Young Talent + Affordability Risk")

    focal_young = df[df["state"] == focal_state].iloc[0] if focal_state else None
    mode_config = get_metric_mode_config()
    col1, col2, col3, col4 = st.columns(4)
    if focal_young is not None:
        with col1:
            st.markdown(metric_card(f"{int(focal_young['young_interstate_in']):,}", "Young In-Migrants (25-34)"), unsafe_allow_html=True)
        with col2:
            st.markdown(metric_card(f"{int(focal_young['young_interstate_out']):,}", "Young Out-Migrants (25-34, est.)"), unsafe_allow_html=True)
        with col3:
            st.markdown(metric_card(format_metric_value(focal_young[mode_config["young_col"]]), mode_config["young_label"]), unsafe_allow_html=True)
        with col4:
            rate = focal_young["rent_burden_30plus_rate"]
            st.markdown(metric_card(f"{rate:.1f}%", "Rent-Burdened Renters (30%+)"), unsafe_allow_html=True)
    else:
        with col1:
            st.markdown(metric_card(f"{int(df['young_interstate_in'].sum()):,}", "Young In-Migrants (25-34)"), unsafe_allow_html=True)
        with col2:
            st.markdown(metric_card(f"{int(df['young_interstate_out'].sum()):,}", "Young Out-Migrants (25-34, est.)"), unsafe_allow_html=True)
        with col3:
            st.markdown(metric_card(format_metric_value(df[mode_config["young_col"]].median()), f"Median {mode_config['young_label']}"), unsafe_allow_html=True)
        with col4:
            st.markdown(metric_card(f"{df['rent_burden_30plus_rate'].median():.1f}%", "Median Rent-Burdened Renters (30%+)"), unsafe_allow_html=True)

    render_section_header(f"{mode_config['young_label']} Ranking")
    df_rank = df[["state", mode_config["young_col"]]].dropna().sort_values(mode_config["young_col"])
    df_rank["color"] = df_rank[mode_config["young_col"]].apply(lambda x: "#c62828" if x < 0 else "#1565c0")
    rank_height = max(1100, len(df_rank) * 28)
    fig_rank = go.Figure(go.Bar(
        x=df_rank[mode_config["young_col"]],
        y=df_rank["state"],
        orientation="h",
        marker_color=df_rank["color"],
        text=df_rank[mode_config["young_col"]].round(2) if mode_config["normalized"] else df_rank[mode_config["young_col"]].round(0),
        textposition="outside",
    ))
    fig_rank.add_vline(x=0, line_width=2, line_color="black")
    fig_rank.update_layout(
        height=rank_height,
        xaxis_title=mode_config["young_axis"],
        yaxis={
            "categoryorder": "total ascending",
            "automargin": True,
            "tickfont": {"size": 12},
        },
        margin=dict(l=180, r=80, t=60, b=60),
        showlegend=False,
    )
    st.plotly_chart(fig_rank, use_container_width=True)

    render_section_header("Cost-Burdened Renters (30%+) by State")
    df_cost = df[["state", "rent_burden_30plus_rate"]].dropna().sort_values("rent_burden_30plus_rate", ascending=False)
    highlight_label = focal_state if focal_state else "Selected State"
    df_cost["Highlight"] = df_cost["state"].apply(lambda s: highlight_label if focal_state and s == focal_state else "Other States")
    fig_cost = px.bar(
        df_cost,
        x="rent_burden_30plus_rate",
        y="state",
        color="Highlight",
        color_discrete_map={highlight_label: "#f9a825", "Other States": "#90a4ae"},
        orientation="h",
        labels={"rent_burden_30plus_rate": "Renter Cost-Burden Rate (30%+)", "state": ""},
        height=900,
        title="Share of Renters Spending 30%+ of Income on Housing",
    )
    fig_cost.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
    st.plotly_chart(fig_cost, use_container_width=True)

    render_section_header("Young Talent + Affordability Diagnostic Table")
    diag_cols = [
        "state",
        "young_interstate_in",
        "young_interstate_out",
        "young_net_migrants",
        "young_inmig_rate",
        "young_outmig_rate",
        "young_net_migration_rate",
        "rent_burden_30plus_rate",
    ]
    diag_df = df[diag_cols].copy().rename(columns={
        "state": "State",
        "young_interstate_in": "Young In-Migrants",
        "young_interstate_out": "Young Out-Migrants (est.)",
        "young_net_migrants": "Young Net Migrants",
        "young_inmig_rate": "Young In-Rate (per 1k)",
        "young_outmig_rate": "Young Out-Rate (per 1k)",
        "young_net_migration_rate": "Young Net Rate (per 1k)",
        "rent_burden_30plus_rate": "Rent Burden Rate 30%+",
    }).round(2)
    diag_df = diag_df.sort_values("Young Net Rate (per 1k)", ascending=False).reset_index(drop=True)
    st.dataframe(
        style_young_diagnostic_table(diag_df),
        use_container_width=True,
        hide_index=True,
    )


#
# MODULE 6: STATE COMPARISON
#
elif analysis_section == " State Comparison Tool":
    st.header(" Side-by-Side State Comparison")

    default_state_a = focal_state or all_states[0]
    default_state_b = next((state for state in all_states if state != default_state_a), all_states[0])
    state_a = st.selectbox(
        "State A",
        all_states,
        index=all_states.index(default_state_a),
    )
    state_b = st.selectbox(
        "Compare With:",
        [s for s in all_states if s != state_a],
        index=max(0, [s for s in all_states if s != state_a].index(default_state_b)) if default_state_b in [s for s in all_states if s != state_a] else 0,
    )
    df_ab = df[df["state"].isin([state_a, state_b])].set_index("state")

    metrics = {
        "Educated In-Migrants": "interstate_in_educated",
        "Educated Out-Migrants (est.)": "interstate_out_educated",
        "Net Educated Migrants": "net_educated_migrants",
        "Net Migration Rate (per 1k)": "net_migration_rate",
        "In-Migration Rate (per 1k)": "edu_inmig_rate",
        "Out-Migration Rate (per 1k)": "edu_outmig_rate",
        "Talent Concentration (%)": "talent_concentration",
        "Educated Stock Total": "stock_educated_total",
        "In-Migrants as % of Stock": "inmig_pct_of_stock",
        "Out-Migrants as % of Stock": "outmig_pct_of_stock",
        "Educated Share of In-Migration (%)": "edu_share_of_inmig",
        "Median Earnings — Bachelor's ($)": "median_earnings_bachelors",
        "Median Earnings — Graduate ($)": "median_earnings_graduate",
        "Policy Segment": "segment",
    }

    rows = []
    for label, col in metrics.items():
        a_val = df_ab.loc[state_a, col] if state_a in df_ab.index and col in df_ab.columns else "N/A"
        b_val = df_ab.loc[state_b, col] if state_b in df_ab.index and col in df_ab.columns else "N/A"
        if isinstance(a_val, float) and isinstance(b_val, float):
            winner = state_a if a_val > b_val else (state_b if b_val > a_val else "Tie")
            # Net migration and lower out-mig is better — mark accordingly
            if "Out-Migr" in label:
                winner = state_a if a_val < b_val else (state_b if b_val < a_val else "Tie")
            a_str = f"{a_val:,.1f}" if "%" in label or "Rate" in label else (f"${a_val:,.0f}" if "$" in label else f"{a_val:,.0f}")
            b_str = f"{b_val:,.1f}" if "%" in label or "Rate" in label else (f"${b_val:,.0f}" if "$" in label else f"{b_val:,.0f}")
        else:
            a_str = str(a_val)
            b_str = str(b_val)
            winner = "—"
        rows.append({"Metric": label, state_a: a_str, state_b: b_str, "Advantage": winner})

    comp_df = pd.DataFrame(rows)
    render_section_header("Comparison summary")
    tab_summary, tab_profile = st.tabs(["Metric table", "Normalized deltas"])
    with tab_summary:
        st.dataframe(comp_df, use_container_width=True, hide_index=True)

    with tab_profile:
        delta_metrics = {
            "Net migration rate": "net_migration_rate",
            "Talent concentration": "talent_concentration",
            "Young net rate": "young_net_migration_rate",
            "Rent burden": "rent_burden_30plus_rate",
            "BA earnings": "median_earnings_bachelors",
            "Educated share": "edu_share_of_inmig",
        }

        def normalize(df_src, col):
            mn, mx = df_src[col].min(), df_src[col].max()
            if mx == mn:
                return pd.Series([50] * len(df_src), index=df_src.index)
            return (df_src[col] - mn) / (mx - mn) * 100

        normalized_df = df[["state", *delta_metrics.values()]].copy()
        for label, col in delta_metrics.items():
            normalized_df[label] = normalize(normalized_df, col)

        plot_rows = []
        for label in delta_metrics.keys():
            plot_rows.append({"Metric": label, "State": state_a, "Score": float(normalized_df.loc[normalized_df["state"] == state_a, label].iloc[0])})
            plot_rows.append({"Metric": label, "State": state_b, "Score": float(normalized_df.loc[normalized_df["state"] == state_b, label].iloc[0])})
        profile_df = pd.DataFrame(plot_rows)
        fig_profile = px.bar(
            profile_df,
            x="Metric",
            y="Score",
            color="State",
            barmode="group",
            color_discrete_map={state_a: get_signal_hsl("positive"), state_b: get_signal_hsl("warning")},
            title=f"{state_a} vs. {state_b} — Normalized profile (0-100)",
            height=500,
        )
        fig_profile.update_layout(
            yaxis_title="Normalized score",
            xaxis_title="",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#eef4ff"),
            legend=dict(font=dict(color="#eef4ff")),
            xaxis=dict(tickfont=dict(color="#d9e2f2")),
            yaxis=dict(tickfont=dict(color="#d9e2f2"), gridcolor="rgba(255,255,255,0.10)"),
        )
        st.plotly_chart(fig_profile, use_container_width=True)

        radar_label_map = {
            "Net migration rate": "Net Migration",
            "Talent concentration": "Talent Conc.",
            "Young net rate": "Young Net",
            "Rent burden": "Rent Burden",
            "BA earnings": "BA Earnings",
            "Educated share": "Edu Share",
        }
        radar_categories = [radar_label_map[label] for label in delta_metrics.keys()]
        radar_a = []
        radar_b = []
        for label in delta_metrics.keys():
            radar_a.append(float(normalized_df.loc[normalized_df["state"] == state_a, label].iloc[0]))
            radar_b.append(float(normalized_df.loc[normalized_df["state"] == state_b, label].iloc[0]))

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=radar_a + [radar_a[0]],
            theta=radar_categories + [radar_categories[0]],
            fill="toself",
            name=state_a,
            line=dict(color=get_signal_hsl("positive"), width=3),
            fillcolor=hsl_color(190, 80, 60, 0.22),
        ))
        fig_radar.add_trace(go.Scatterpolar(
            r=radar_b + [radar_b[0]],
            theta=radar_categories + [radar_categories[0]],
            fill="toself",
            name=state_b,
            line=dict(color=get_signal_hsl("warning"), width=3),
            fillcolor=hsl_color(38, 84, 62, 0.22),
        ))
        fig_radar.update_layout(
            title=f"{state_a} vs. {state_b} — Radar profile",
            height=520,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#eef4ff"),
            legend=dict(font=dict(color="#eef4ff")),
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                angularaxis=dict(
                    color="#eef4ff",
                    gridcolor="rgba(255,255,255,0.10)",
                    linecolor="rgba(255,255,255,0.16)",
                ),
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(color="#d9e2f2"),
                    gridcolor="rgba(255,255,255,0.14)",
                    linecolor="rgba(255,255,255,0.18)",
                ),
            ),
        )
        st.plotly_chart(fig_radar, use_container_width=True)


#
# MODULE 7: GOVERNOR'S BRIEFING
#
elif analysis_section == " Governor's Briefing":
    if focal_state is None:
        st.header(" Governor's Briefing")
        st.info("Choose a state in the sidebar to generate a governor's briefing.")
    else:
        st.header(f" Governor's Briefing: {focal_state}")

        focal = df[df["state"] == focal_state].iloc[0]

        # Headline KPIs
        cols = st.columns(4)
        kpis = [
            (f"{int(focal['interstate_in_educated']):,}", "Educated In-Migrants"),
            (f"{int(focal['interstate_out_educated']):,}", "Educated Out-Migrants (est.)"),
            (f"{focal['net_educated_migrants']:+,.0f}", "Net Educated Migration"),
            (focal["segment"], "Policy Segment"),
        ]
        for c, (v, l) in zip(cols, kpis):
            c.markdown(metric_card(v, l), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Data summary box
        net = focal["net_educated_migrants"]
        conc = focal["talent_concentration"]
        nat_net = df["net_educated_migrants"].median()
        nat_conc = df["talent_concentration"].median()
        narrative = (
            f"**{focal_state} data snapshot:** Net educated migration is {net:+,.0f} versus a national median of "
            f"{nat_net:+,.0f}. Talent concentration is {conc:.1f}% versus a national median of {nat_conc:.1f}%. "
            f"Young net migration rate is {focal['young_net_migration_rate']:+.2f} per 1,000, and renter cost burden "
            f"is {focal['rent_burden_30plus_rate']:.1f}%."
        )

        render_section_header("Executive summary")
        st.markdown(f'<div class="policy-box"><h4> Executive Data Summary</h4><p>{narrative}</p></div>', unsafe_allow_html=True)
        if AI_AVAILABLE:
            briefing_key = get_briefing_cache_key(focal_state)
            briefing_context = build_briefing_context(df, focal_state)
            deterministic_briefing = build_deterministic_briefing_payload(df, focal_state)
            with st.container(border=True):
                action_cols = st.columns([1, 1, 6])
                if action_cols[0].button("Generate AI Briefing", key=f"{briefing_key}_generate"):
                    try:
                        st.session_state[briefing_key] = generate_briefing(GEMINI_API_KEY, briefing_context).model_dump()
                    except GroundingValidationError as exc:
                        st.session_state[briefing_key] = {"fallback": deterministic_briefing, "error": str(exc)}
                    except Exception as exc:
                        st.session_state[briefing_key] = {"error": str(exc), "fallback": deterministic_briefing}
                if action_cols[1].button("Refresh Briefing", key=f"{briefing_key}_refresh"):
                    st.session_state.pop(briefing_key, None)
                    try:
                        st.session_state[briefing_key] = generate_briefing(GEMINI_API_KEY, briefing_context).model_dump()
                    except GroundingValidationError as exc:
                        st.session_state[briefing_key] = {"fallback": deterministic_briefing, "error": str(exc)}
                    except Exception as exc:
                        st.session_state[briefing_key] = {"error": str(exc), "fallback": deterministic_briefing}

            if briefing_key in st.session_state:
                payload = st.session_state[briefing_key]
                with st.container(border=True):
                    render_section_header("AI Governor Briefing")
                    ai_caption()
                    if "headline" in payload:
                        render_briefing_payload(payload)
                        st.caption("Data used: focal state metrics, national medians, and ranks from this dashboard")
                        st.caption("Tool path: `generate_briefing`")
                    else:
                        if payload.get("error"):
                            st.caption(f"AI unavailable: {payload['error']}")
                        if payload.get("fallback"):
                            render_briefing_payload(payload["fallback"], deterministic=True)
                            st.caption("Data used: focal state metrics, national medians, and ranks from this dashboard")
                            st.caption("Tool path: `deterministic_briefing_fallback`")
                        else:
                            st.info("The app could not generate a briefing for this state.")

                    render_section_header("Briefing visual summary")
                    briefing_visual_df, policy_segment = build_briefing_visual_df(df, focal_state)
                    render_helper_note("The dashed line marks a relative national-standing score of 50, which represents the U.S. median. The table below shows the exact U.S. median for each metric and whether higher or lower values are better.")
                    visual_cols = st.columns([1.2, 3.8])
                    with visual_cols[0]:
                        segment_signal = "positive" if policy_segment in {"Talent Hub", "Rising Gainer"} else "negative"
                        segment_color = get_signal_hsl(segment_signal)
                        st.markdown(
                            (
                                '<div class="summary-stat" style="border-color: rgba(255,255,255,0.16);">'
                                '<div class="label">Policy segment</div>'
                                f'<div class="value" style="color: {segment_color};">{policy_segment}</div>'
                                '<div class="label">Based on migration strength and talent concentration.</div>'
                                '</div>'
                            ),
                            unsafe_allow_html=True,
                        )
                    with visual_cols[1]:
                        fig_briefing = px.bar(
                            briefing_visual_df,
                            x="PercentileScore",
                            y="Metric",
                            color="Metric",
                            orientation="h",
                            text="Display",
                            color_discrete_map={
                                row["Metric"]: row["Color"]
                                for _, row in briefing_visual_df.iterrows()
                            },
                            height=420,
                        )
                        fig_briefing.update_traces(
                            textposition="outside",
                            cliponaxis=False,
                            width=0.52,
                        )
                        fig_briefing.add_vline(x=50, line_dash="dash", line_color="rgba(255,255,255,0.4)")
                        for _, row in briefing_visual_df.iterrows():
                            fig_briefing.add_annotation(
                                x=50,
                                y=row["Metric"],
                                text="Median",
                                showarrow=False,
                                xshift=18,
                                font=dict(color="rgba(217,226,242,0.75)", size=10),
                            )
                        fig_briefing.update_layout(
                            showlegend=False,
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#eef4ff"),
                            margin=dict(l=20, r=90, t=12, b=40),
                            xaxis=dict(
                                title="Relative national standing (0-100)",
                                range=[0, 100],
                                tickfont=dict(color="#d9e2f2"),
                                gridcolor="rgba(255,255,255,0.10)",
                                zeroline=False,
                            ),
                            yaxis=dict(
                                title="",
                                tickfont=dict(color="#eef4ff"),
                                categoryorder="array",
                                categoryarray=list(reversed(briefing_visual_df["Metric"].tolist())),
                            ),
                        )
                        st.plotly_chart(fig_briefing, use_container_width=True)
                        st.dataframe(
                            briefing_visual_df[["Metric", "Display", "MedianDisplay", "BetterWhen"]].rename(
                                columns={
                                    "Display": "State value",
                                    "MedianDisplay": "U.S. median",
                                    "BetterWhen": "Interpretation",
                                }
                            ),
                            use_container_width=True,
                            hide_index=True,
                        )

        # Raw stats table
        focal_metrics = {
            "Educated In-Migrants (BA+)": f"{int(focal['interstate_in_educated']):,}",
            "Educated Out-Migrants — est. (BA+)": f"{int(focal['interstate_out_educated']):,}",
            "Net Educated Migration": f"{focal['net_educated_migrants']:+,.0f}",
            "In-Migration Rate (per 1k 25+)": f"{focal['edu_inmig_rate']:.2f}",
            "Out-Migration Rate (per 1k 25+)": f"{focal['edu_outmig_rate']:.2f}",
            "Net Migration Rate (per 1k 25+)": f"{focal['net_migration_rate']:.2f}",
            "Total Educated Stock (BA+)": f"{int(focal['stock_educated_total']):,}",
            "Talent Concentration (%)": f"{focal['talent_concentration']:.1f}%",
            "In-Migrants as % of Educated Stock": f"{focal['inmig_pct_of_stock']:.2f}%",
            "Out-Migrants as % of Educated Stock": f"{focal['outmig_pct_of_stock']:.2f}%",
            "Median Earnings — All Workers ($)": f"${focal['median_earnings_total']:,.0f}",
            "Median Earnings — Bachelor's ($)": f"${focal['median_earnings_bachelors']:,.0f}",
            "Median Earnings — Graduate ($)": f"${focal['median_earnings_graduate']:,.0f}",
            "Policy Segment": focal["segment"],
        }
        render_section_header(f"Full Metrics For {focal_state}")
        st.dataframe(pd.DataFrame(focal_metrics.items(), columns=["Metric", "Value"]),
                     use_container_width=True, hide_index=True)


#
# MODULE 8: METHODOLOGY
#
elif analysis_section == " Methodology & Limitations":
    st.header(" Methodology & Data Limitations")

    st.markdown("""
    <div class="policy-box">
    <h4> Data Sources (All ACS 5-Year Estimates)</h4>
    <ul>
    <li><b>B07009</b> — Geographical Mobility by Educational Attainment (current residence). Used for educated in-migration counts.
        Interstate in-migrants = "Moved from different state" rows (_025E total, _029E bachelor's, _030E graduate/professional).</li>
    <li><b>B07409</b> — Geographical Mobility by Educational Attainment (residence 1 year ago). Used as a <em>proxy</em> for out-migration.
        This captures people whose prior-year address was in a given state and who moved away.</li>
    <li><b>B15003</b> — Educational Attainment for Population 25+. Provides the "stock" of degree holders as the denominator
        for concentration and drain calculations (_022E BA, _023E MA, _024E Professional, _025E Doctorate).</li>
    <li><b>B20004</b> — Median Earnings by Sex by Educational Attainment. Used for wage competitiveness analysis
        (_005E bachelor's earnings, _006E graduate earnings).</li>
    <li><b>B07001</b> — Geographical Mobility by Age (current residence). Used for young interstate in-migration
        ages 25-34 (25-29 + 30-34 bins).</li>
    <li><b>B07401</b> — Geographical Mobility by Age (residence 1 year ago). Used as a <em>proxy</em> for young
        interstate out-migration ages 25-34.</li>
    <li><b>B25070</b> — Gross Rent as a Percentage of Household Income. Used to compute renter cost-burden pressure
        (share spending 30%+ of income on rent).</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="warn-box">
    <h4> Critical Interpretation Flags</h4>
    <p><b>1. In-migration vs. Net Migration:</b> B07009 captures people who <em>arrived</em> in a state from another state.
    It does not capture who left. B07409 (prior-year residence) is the best proxy for out-migration but is not a perfect
    complement — methodological differences exist between the two tables. Net figures are directional estimates.</p>

    <p><b>2. Young cohort measurement:</b> Young-talent metrics use B07001/B07401 age bins 25-29 and 30-34. This improves
    age specificity versus the 25+ educated flow metrics, but still excludes younger movers under 25 and does not isolate
    degree status within the young-only module.</p>

    <p><b>3. Safe terminology:</b> Use "educated in-migration", "young net migration", and "estimated net migration."
    Avoid asserting "brain drain"
    as a confirmed fact — this analysis identifies <em>risk indicators</em>, not causation.</p>

    <p><b>4. Earnings (B20004):</b> These are median earnings for workers with earnings — not all residents.
    They reflect current state market conditions and may understate remote-worker income if that worker moved for lifestyle reasons.</p>

    <p><b>5. Affordability proxy limits:</b> B25070 reflects renter households, not owners. Cost-burden rates do not
    represent full cost-of-living, and they do not include wages directly.</p>

    <p><b>6. ACS 5-Year estimates:</b> These are period estimates (e.g., 2018–2022), not single-year snapshots.
    They are best for structural comparisons, not tracking year-over-year changes.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="policy-box">
    <h4> Computed Metrics</h4>
    <ul>
    <li><b>Net Educated Migration</b> = Interstate In-Migrants (educated) − Interstate Out-Migrants est. (educated)</li>
    <li><b>Migration Rates</b> = (migrants / pop_25plus) × 1,000</li>
    <li><b>Young In-Migration (25-34)</b> = B07001_070E + B07001_071E</li>
    <li><b>Young Out-Migration est. (25-34)</b> = B07401_070E + B07401_071E</li>
    <li><b>Young Net Migration Rate</b> = ((young in − young out) / young pop 25-34) × 1,000</li>
    <li><b>Rent-Burden Rate (30%+)</b> = (B25070_007E + _008E + _009E + _010E) / (B25070_001E − B25070_011E) × 100</li>
    <li><b>Talent Concentration</b> = (BA+ stock / total pop 25+) × 100</li>
    <li><b>Migration as % of Stock</b> = (migrants / BA+ stock) × 100 — key brain drain signal</li>
    <li><b>Educated Share of Migration</b> = (educated migrants / all migrants) × 100 — quality signal</li>
    <li><b>Policy Segments</b>: Based on median splits of net migration rate and talent concentration:
        Talent Hub (high/high), Rising Gainer (high/low), At-Risk Retainer (low/high), Brain Drain Risk (low/low)</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
