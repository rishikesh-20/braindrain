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
    .metric-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d6a9f 100%);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .metric-card h2 { font-size: 2rem; margin: 0; font-weight: 700; }
    .metric-card p  { font-size: 0.85rem; margin: 0.3rem 0 0; opacity: 0.9; }
    .metric-card .metric-desc { font-size: 0.76rem; margin-top: 0.45rem; opacity: 0.88; line-height: 1.25; }
    .metric-card .metric-formula { font-size: 0.68rem; margin-top: 0.35rem; opacity: 0.72; line-height: 1.2; }
    .policy-box {
        background: #111827;
        border-left: 5px solid #2d6a9f;
        border-radius: 0 8px 8px 0;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        color: #ffffff;
    }
    .policy-box h4 { color: #90caf9; margin-top: 0; }
    .policy-box p, .policy-box li, .policy-box ul { color: #ffffff; }
    .policy-box b { color: #90caf9; }
    .warn-box {
        background: #1a1200;
        border-left: 5px solid #f9a825;
        border-radius: 0 8px 8px 0;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        color: #ffffff;
    }
    .warn-box h4 { color: #ffd54f; margin-top: 0; }
    .warn-box p, .warn-box li, .warn-box b { color: #ffffff; }
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e3a5f;
        border-bottom: 2px solid #2d6a9f;
        padding-bottom: 0.4rem;
        margin: 1.5rem 0 1rem;
    }
</style>
""", unsafe_allow_html=True)

#
# API Key
#
API_KEY = st.secrets["CENSUS_API_KEY"]

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
    focal_state = st.selectbox(" Focal State", all_states,
                               index=all_states.index("North Carolina") if "North Carolina" in all_states else 0)

    st.caption("Metric Mode: Normalized (per 1k)")

    st.divider()
    st.caption("**Data Sources:**\nACS 5-Year Estimates\n• B07009 (in-migration)\n• B07409 (out-migration proxy)\n• B15003 (education stock)\n• B20004 (median earnings)")


#
# HELPER: metric card HTML
#
def metric_card(value, label, description=None, formula=None):
    description_html = f'<div class="metric-desc">{description}</div>' if description else ""
    formula_html = f'<div class="metric-formula">{formula}</div>' if formula else ""
    return f"""<div class="metric-card"><h2>{value}</h2><p>{label}</p>{description_html}{formula_html}</div>"""


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


def get_metric_mode_config():
    return {
        "normalized": True,
        "educated_col": "net_migration_rate",
        "educated_label": "Educated Net Rate (per 1k)",
        "educated_axis": "Educated Net Migration Rate (per 1k)",
        "young_col": "young_net_migration_rate",
        "young_label": "Young Net Rate (25-34, per 1k)",
        "young_axis": "Young Net Migration Rate (per 1k, ages 25-34)",
        "mode_suffix": "Rate",
    }


#
# MODULE 1: EXECUTIVE DASHBOARD
#
if analysis_section == " Executive Dashboard":
    st.title("Brain Drain Intelligence Platform")
    st.markdown("**Team 2 — Economic Policy Advisors to the Governor** | ACS 5-Year Estimates")

    focal = df[df["state"] == focal_state].iloc[0]
    mode_config = get_metric_mode_config()

    # KPI Row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(metric_card(
            f"{int(focal['interstate_in_educated']):,}",
            "Educated In-Migrants",
            "People with a bachelor's or higher who moved into the state.",
            "BA movers in + graduate movers in",
        ), unsafe_allow_html=True)
    with col2:
        st.markdown(metric_card(
            f"{int(focal['interstate_out_educated']):,}",
            "Educated Out-Migrants (est.)",
            "People with a bachelor's or higher estimated to have moved out.",
            "BA movers out + graduate movers out",
        ), unsafe_allow_html=True)
    with col3:
        net = int(focal['net_educated_migrants'])
        color = "#2e7d32" if net >= 0 else "#c62828"
        st.markdown(f"""<div class="metric-card" style="background: linear-gradient(135deg, {color} 0%, {'#43a047' if net>=0 else '#e53935'} 100%);">
            <h2>{net:+,}</h2><p>Net Educated Migration</p>
            <div class="metric-desc">The balance between educated arrivals and educated departures.</div>
            <div class="metric-formula">educated in-migrants - educated out-migrants</div></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(metric_card(
            f"{focal['talent_concentration']:.1f}%",
            "Talent Concentration",
            "Share of adults who already hold at least a bachelor's degree.",
            "educated stock / adults 25+ x 100",
        ), unsafe_allow_html=True)
    with col5:
        st.markdown(metric_card(
            focal['segment'],
            "Policy Segment",
            "A quick label showing the state's migration and talent position.",
            "based on net migration rate + talent concentration",
        ), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Decision scorecard for presentation
    st.markdown('<div class="section-header">Brain Drain Decision Scorecard (Focal State)</div>', unsafe_allow_html=True)
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(metric_card(
            format_metric_value(focal[mode_config["educated_col"]]),
            mode_config["educated_label"],
            "Net gain or loss of educated people after adjusting for state size.",
            "(educated in - educated out) / adults 25+ x 1,000",
        ), unsafe_allow_html=True)
    with s2:
        st.markdown(metric_card(
            format_metric_value(focal[mode_config["young_col"]]),
            mode_config["young_label"],
            "Net gain or loss of adults ages 25 to 34 after adjusting for cohort size.",
            "(young in - young out) / population 25-34 x 1,000",
        ), unsafe_allow_html=True)
    with s3:
        st.markdown(metric_card(
            f"{focal['rent_burden_30plus_rate']:.1f}%",
            "Rent Burden (30%+)",
            "Share of renters spending at least 30% of income on housing.",
            "rent-burdened renters / renter households x 100",
        ), unsafe_allow_html=True)
    with s4:
        st.markdown(metric_card(
            f"${focal['bachelors_earnings_premium']:,.0f}",
            "BA Earnings Premium",
            "How much more bachelor's degree holders earn than the average worker.",
            "BA median earnings - overall median earnings",
        ), unsafe_allow_html=True)

    if focal["net_migration_rate"] >= 0 and focal["young_net_migration_rate"] < 0:
        st.markdown("""
        <div class="warn-box">
        <b>Signal Divergence:</b> Educated net migration is positive, but young (25-34) net migration is negative.
        This is a direct comparison of two ACS-derived metrics.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Quadrant scatter
    st.markdown('<div class="section-header">National Talent Positioning Map</div>', unsafe_allow_html=True)
    st.caption(f"X-axis = {mode_config['educated_axis']} | Y-axis = Talent concentration % | Size = education stock")
    color_map = {
        "Talent Hub": "#1565c0",
        "Rising Gainer": "#2e7d32",
        "At-Risk Retainer": "#f57c00",
        "Brain Drain Risk": "#c62828",
    }

    fig_quad = px.scatter(
        df,
        x=mode_config["educated_col"],
        y="talent_concentration",
        size="stock_educated_total",
        color="segment",
        color_discrete_map=color_map,
        hover_name="state",
        hover_data={
            mode_config["educated_col"]: ":.2f" if mode_config["normalized"] else ":,",
            "talent_concentration": ":.1f",
            "net_educated_migrants": ":,",
            "stock_educated_total": ":,",
            "segment": False,
        },
        labels={
            mode_config["educated_col"]: mode_config["educated_axis"],
            "talent_concentration": "Talent Concentration (%)",
            "stock_educated_total": "Total Educated Stock",
        },
        title=f"State Talent Positioning: {mode_config['educated_label']} vs. Talent Concentration",
        height=520,
    )
    # Quadrant lines
    fig_quad.add_hline(y=df["talent_concentration"].median(), line_dash="dash", line_color="gray", opacity=0.5)
    fig_quad.add_vline(x=df[mode_config["educated_col"]].median(), line_dash="dash", line_color="gray", opacity=0.5)
    # Highlight focal state
    focal_row = df[df["state"] == focal_state]
    fig_quad.add_scatter(
        x=focal_row[mode_config["educated_col"]], y=focal_row["talent_concentration"],
        mode="markers+text", text=[focal_state], textposition="top right",
        marker=dict(size=18, color="gold", line=dict(width=2, color="black")),
        showlegend=False, name=focal_state,
    )
    fig_quad.update_layout(legend_title="Policy Segment")
    st.plotly_chart(fig_quad, use_container_width=True)

    # Altair choropleth: net educated migration rate by state
    st.markdown('<div class="section-header">Geographic Brain Drain Signal (Choropleth)</div>', unsafe_allow_html=True)
    st.caption(f"Diverging scale centered at zero: red = net talent loss, blue = net talent gain. Current view: {mode_config['educated_label']}.")

    map_df = df[["state", mode_config["educated_col"], "segment", "talent_concentration", "net_educated_migrants"]].copy()
    map_df["id"] = map_df["state"].apply(lambda s: us.states.lookup(s).fips if us.states.lookup(s) else None)
    map_df = map_df.dropna(subset=["id", mode_config["educated_col"]])
    map_df["id"] = map_df["id"].astype(str).str.zfill(2)
    max_abs_rate = float(map_df[mode_config["educated_col"]].abs().max()) if not map_df.empty else 1.0
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
                ["state", mode_config["educated_col"], "segment", "talent_concentration", "net_educated_migrants"],
            ),
        )
        .encode(
            color=alt.Color(
                f"{mode_config['educated_col']}:Q",
                title=mode_config["educated_label"],
                scale=alt.Scale(scheme="redblue", domain=[-max_abs_rate, max_abs_rate]),
            ),
            tooltip=[
                alt.Tooltip("state:N", title="State"),
                alt.Tooltip(f"{mode_config['educated_col']}:Q", title=mode_config["educated_label"], format=".2f" if mode_config["normalized"] else ",.0f"),
                alt.Tooltip("net_educated_migrants:Q", title="Net Migrants", format=",.0f"),
                alt.Tooltip("talent_concentration:Q", title="Talent Concentration (%)", format=".1f"),
                alt.Tooltip("segment:N", title="Segment"),
            ],
        )
        .project(type="albersUsa")
        .properties(height=500)
    )

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
        .transform_filter(alt.datum.state == focal_state)
        .project(type="albersUsa")
    )

    st.altair_chart(alt.layer(base_states, choropleth, focal_outline), use_container_width=True)

    # Peer benchmarking
    st.markdown('<div class="section-header">Peer Benchmarking (5-State Comparator Set)</div>', unsafe_allow_html=True)
    st.caption("Select up to 5 comparison states manually. No peers are auto-generated.")
    selected_peers = st.multiselect(
        "Peer States",
        options=[s for s in all_states if s != focal_state],
        default=[],
        max_selections=5,
    )
    benchmark_states = [focal_state] + selected_peers
    bench = df[df["state"].isin(benchmark_states)].copy()

    rank_net = df[mode_config["educated_col"]].rank(ascending=False, method="min")
    rank_young = df[mode_config["young_col"]].rank(ascending=False, method="min")
    rank_rent = df["rent_burden_30plus_rate"].rank(ascending=True, method="min")
    rank_premium = df["bachelors_earnings_premium"].rank(ascending=False, method="min")
    national_medians = {
        mode_config["educated_col"]: df[mode_config["educated_col"]].median(),
        mode_config["young_col"]: df[mode_config["young_col"]].median(),
        "rent_burden_30plus_rate": df["rent_burden_30plus_rate"].median(),
        "bachelors_earnings_premium": df["bachelors_earnings_premium"].median(),
    }

    bench["Rank Net"] = bench.index.map(rank_net)
    bench["Rank Young"] = bench.index.map(rank_young)
    bench["Rank Rent"] = bench.index.map(rank_rent)
    bench["Rank Premium"] = bench.index.map(rank_premium)
    bench["Gap vs US Median (Net)"] = bench[mode_config["educated_col"]] - national_medians[mode_config["educated_col"]]
    bench["Gap vs US Median (Young)"] = bench[mode_config["young_col"]] - national_medians[mode_config["young_col"]]
    bench["Gap vs US Median (Rent)"] = bench["rent_burden_30plus_rate"] - national_medians["rent_burden_30plus_rate"]
    bench["Gap vs US Median (Premium)"] = bench["bachelors_earnings_premium"] - national_medians["bachelors_earnings_premium"]

    benchmark_table = bench[
        [
            "state",
            mode_config["educated_col"],
            mode_config["young_col"],
            "rent_burden_30plus_rate",
            "bachelors_earnings_premium",
            "Rank Net",
            "Rank Young",
            "Rank Rent",
            "Rank Premium",
            "Gap vs US Median (Net)",
            "Gap vs US Median (Young)",
            "Gap vs US Median (Rent)",
            "Gap vs US Median (Premium)",
        ]
    ].copy()
    benchmark_table.columns = [
        "State",
        mode_config["educated_label"],
        mode_config["young_label"],
        "Rent Burden (30%+)",
        "BA Earnings Premium ($)",
        "Rank: Net",
        "Rank: Young",
        "Rank: Rent (lower better)",
        "Rank: Premium",
        "Gap to US Median: Net",
        "Gap to US Median: Young",
        "Gap to US Median: Rent",
        "Gap to US Median: Premium",
    ]
    st.dataframe(benchmark_table.round(2), use_container_width=True, hide_index=True)

    gap_chart = bench[["state", "Gap vs US Median (Net)", "Gap vs US Median (Young)", "Gap vs US Median (Rent)"]].melt(
        id_vars="state",
        var_name="Metric",
        value_name="Gap",
    )
    gap_chart["Metric"] = gap_chart["Metric"].map({
        "Gap vs US Median (Net)": "Net Rate Gap",
        "Gap vs US Median (Young)": "Young Net Gap",
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

    st.markdown('<div class="section-header">Potential Brain Drain Drivers</div>', unsafe_allow_html=True)
    left_col, right_col = st.columns(2)

    with left_col:
        df_young_exec = df.dropna(subset=[mode_config["young_col"], "rent_burden_30plus_rate", "young_pop_25_34"]).copy()
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
        focal_row_exec = df_young_exec[df_young_exec["state"] == focal_state]
        if not focal_row_exec.empty:
            fig_young_housing_exec.add_scatter(
                x=focal_row_exec["rent_burden_30plus_rate"],
                y=focal_row_exec[mode_config["young_col"]],
                mode="markers+text",
                text=[focal_state],
                textposition="top right",
                marker=dict(size=16, color="gold", line=dict(width=2, color="black")),
                showlegend=False,
        )
        fig_young_housing_exec.update_layout(showlegend=True)
        st.plotly_chart(fig_young_housing_exec, use_container_width=True)
        st.caption("Positive means the state gained young adults ages 25-34; negative means it lost them.")

    with right_col:
        df_earn = df.dropna(subset=["median_earnings_bachelors", "net_migration_rate"]).copy()
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
        focal_row_earn = df_earn[df_earn["state"] == focal_state]
        if not focal_row_earn.empty:
            fig_earn.add_scatter(
                x=focal_row_earn["median_earnings_bachelors"],
                y=focal_row_earn["net_migration_rate"],
                mode="markers+text",
                text=[focal_state],
                textposition="top right",
                marker=dict(size=16, color="gold", line=dict(width=2, color="black")),
                showlegend=False,
        )
        fig_earn.update_layout(showlegend=True)
        st.plotly_chart(fig_earn, use_container_width=True)
        st.caption("Positive means the state gained educated people overall; negative means it lost them.")


#
# MODULE 5: STATE COMPARISON
#
elif analysis_section == " Young Talent + Affordability Risk":
    st.header(" Young Talent + Affordability Risk")
    st.caption("Adds ages 25-34 interstate movement (B07001/B07401) and renter cost-burden pressure (B25070).")

    focal_young = df[df["state"] == focal_state].iloc[0]
    mode_config = get_metric_mode_config()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(metric_card(f"{int(focal_young['young_interstate_in']):,}", "Young In-Migrants (25-34)"), unsafe_allow_html=True)
    with col2:
        st.markdown(metric_card(f"{int(focal_young['young_interstate_out']):,}", "Young Out-Migrants (25-34, est.)"), unsafe_allow_html=True)
    with col3:
        st.markdown(metric_card(format_metric_value(focal_young[mode_config["young_col"]]), mode_config["young_label"]), unsafe_allow_html=True)
    with col4:
        rate = focal_young["rent_burden_30plus_rate"]
        st.markdown(metric_card(f"{rate:.1f}%", "Rent-Burdened Renters (30%+)"), unsafe_allow_html=True)

    st.markdown(f'<div class="section-header">{mode_config["young_label"]} Ranking</div>', unsafe_allow_html=True)
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

    st.markdown('<div class="section-header">Cost-Burdened Renters (30%+) by State</div>', unsafe_allow_html=True)
    df_cost = df[["state", "rent_burden_30plus_rate"]].dropna().sort_values("rent_burden_30plus_rate", ascending=False)
    df_cost["Highlight"] = df_cost["state"].apply(lambda s: focal_state if s == focal_state else "Other States")
    fig_cost = px.bar(
        df_cost,
        x="rent_burden_30plus_rate",
        y="state",
        color="Highlight",
        color_discrete_map={focal_state: "#f9a825", "Other States": "#90a4ae"},
        orientation="h",
        labels={"rent_burden_30plus_rate": "Renter Cost-Burden Rate (30%+)", "state": ""},
        height=900,
        title="Share of Renters Spending 30%+ of Income on Housing",
    )
    fig_cost.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
    st.plotly_chart(fig_cost, use_container_width=True)

    st.markdown('<div class="section-header">Young Talent + Affordability Diagnostic Table</div>', unsafe_allow_html=True)
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
    st.dataframe(diag_df.sort_values("Young Net Rate (per 1k)"),
                 use_container_width=True, hide_index=True)


#
# MODULE 6: STATE COMPARISON
#
elif analysis_section == " State Comparison Tool":
    st.header(" Side-by-Side State Comparison")

    state_a = focal_state
    state_b = st.selectbox(
        "Compare With:",
        [s for s in all_states if s != state_a],
        index=0,
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
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

    # Radar / spider chart
    st.markdown('<div class="section-header">Normalized Performance Radar</div>', unsafe_allow_html=True)
    radar_metrics = {
        "Net Migration Rate": "net_migration_rate",
        "In-Migration Rate": "edu_inmig_rate",
        "Talent Concentration": "talent_concentration",
        "Educated Stock": "stock_educated_total",
        "BA Earnings": "median_earnings_bachelors",
        "Edu Share of Migration": "edu_share_of_inmig",
    }

    def normalize(df_src, col):
        mn, mx = df_src[col].min(), df_src[col].max()
        return (df_src.loc[df_src["state"].isin([state_a, state_b]), col] - mn) / (mx - mn) * 100

    cats = list(radar_metrics.keys())
    vals_a = [normalize(df, v).loc[df["state"] == state_a].values[0] if not normalize(df, v).loc[df["state"] == state_a].empty else 0 for v in radar_metrics.values()]
    vals_b = [normalize(df, v).loc[df["state"] == state_b].values[0] if not normalize(df, v).loc[df["state"] == state_b].empty else 0 for v in radar_metrics.values()]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(r=vals_a + [vals_a[0]], theta=cats + [cats[0]], fill="toself",
                                         name=state_a, line_color="#1565c0", opacity=0.6))
    fig_radar.add_trace(go.Scatterpolar(r=vals_b + [vals_b[0]], theta=cats + [cats[0]], fill="toself",
                                         name=state_b, line_color="#c62828", opacity=0.6))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                            title=f"{state_a} vs. {state_b} — Normalized Performance", height=500)
    st.plotly_chart(fig_radar, use_container_width=True)


#
# MODULE 7: GOVERNOR'S BRIEFING
#
elif analysis_section == " Governor's Briefing":
    st.header(f" Governor's Briefing: {focal_state}")
    st.markdown("*A data-based executive summary for the selected state.*")

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

    st.markdown(f'<div class="policy-box"><h4> Executive Data Summary</h4><p>{narrative}</p></div>', unsafe_allow_html=True)

    # Raw stats table
    st.markdown('<div class="section-header">Full Metrics for ' + focal_state + '</div>', unsafe_allow_html=True)
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
