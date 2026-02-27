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
import plotly.express as px
import plotly.graph_objects as go
from census import Census

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
    .metric-card p  { font-size: 0.85rem; margin: 0.3rem 0 0; opacity: 0.85; }
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


@st.cache_data(show_spinner="Assembling master dataset…")
def load_master():
    """
    Joins all four tables and computes advanced policy metrics.
    """
    b7 = load_b07009()
    b7_out = load_b07409()
    b15 = load_b15003()
    b20 = load_b20004()

    df = b7.merge(b7_out, on="state", how="left")
    df = df.merge(b15, on="state", how="left")
    df = df.merge(b20, on="state", how="left")

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

    #  Policy labels
    nat_median_rate = df["net_migration_rate"].median()
    nat_median_conc = df["talent_concentration"].median()

    def segment(row):
        high_net = row["net_migration_rate"] > nat_median_rate
        high_conc = row["talent_concentration"] > nat_median_conc
        if high_net and high_conc:
            return " Talent Hub"
        elif high_net and not high_conc:
            return " Rising Gainer"
        elif not high_net and high_conc:
            return " At-Risk Retainer"
        else:
            return " Brain Drain Risk"

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
            " Talent Flow: Inflow vs Outflow",
            " Income & Talent Correlation",
            " Education Stock & Concentration",
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

    metric_mode = st.radio(" Metric Mode", ["Normalized (per 1k)", "Absolute Count"], horizontal=True)

    st.divider()
    st.caption("**Data Sources:**\nACS 5-Year Estimates\n• B07009 (in-migration)\n• B07409 (out-migration proxy)\n• B15003 (education stock)\n• B20004 (median earnings)")


#
# HELPER: metric card HTML
#
def metric_card(value, label):
    return f"""<div class="metric-card"><h2>{value}</h2><p>{label}</p></div>"""


#
# MODULE 1: EXECUTIVE DASHBOARD
#
if analysis_section == " Executive Dashboard":
    st.title(" Brain Drain Intelligence Platform")
    st.markdown("**Team 2 — Economic Policy Advisors to the Governor** | ACS 5-Year Estimates")

    focal = df[df["state"] == focal_state].iloc[0]

    # KPI Row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(metric_card(f"{int(focal['interstate_in_educated']):,}", "Educated In-Migrants"), unsafe_allow_html=True)
    with col2:
        st.markdown(metric_card(f"{int(focal['interstate_out_educated']):,}", "Educated Out-Migrants (est.)"), unsafe_allow_html=True)
    with col3:
        net = int(focal['net_educated_migrants'])
        color = "#2e7d32" if net >= 0 else "#c62828"
        st.markdown(f"""<div class="metric-card" style="background: linear-gradient(135deg, {color} 0%, {'#43a047' if net>=0 else '#e53935'} 100%);">
            <h2>{net:+,}</h2><p>Net Educated Migration</p></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(metric_card(f"{focal['talent_concentration']:.1f}%", "Talent Concentration"), unsafe_allow_html=True)
    with col5:
        st.markdown(metric_card(focal['segment'], "Policy Segment"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Quadrant scatter
    st.markdown('<div class="section-header">National Talent Positioning Map</div>', unsafe_allow_html=True)
    st.caption("X-axis = Net migration rate (in minus out per 1k) | Y-axis = Talent concentration % | Size = education stock")

    highlight_col = df["state"].apply(lambda s: " Focal State" if s == focal_state else focal["segment"] if s == focal_state else df.loc[df["state"]==s, "segment"].values[0])
    color_map = {
        " Talent Hub": "#1565c0",
        " Rising Gainer": "#2e7d32",
        " At-Risk Retainer": "#f57c00",
        " Brain Drain Risk": "#c62828",
    }

    fig_quad = px.scatter(
        df,
        x="net_migration_rate",
        y="talent_concentration",
        size="stock_educated_total",
        color="segment",
        color_discrete_map=color_map,
        hover_name="state",
        hover_data={
            "net_migration_rate": ":.2f",
            "talent_concentration": ":.1f",
            "net_educated_migrants": ":,",
            "stock_educated_total": ":,",
            "segment": False,
        },
        labels={
            "net_migration_rate": "Net Educated Migration Rate (per 1k)",
            "talent_concentration": "Talent Concentration (%)",
            "stock_educated_total": "Total Educated Stock",
        },
        title="State Talent Positioning: Net Migration Rate vs. Talent Concentration",
        height=520,
    )
    # Quadrant lines
    fig_quad.add_hline(y=df["talent_concentration"].median(), line_dash="dash", line_color="gray", opacity=0.5)
    fig_quad.add_vline(x=df["net_migration_rate"].median(), line_dash="dash", line_color="gray", opacity=0.5)
    # Highlight focal state
    focal_row = df[df["state"] == focal_state]
    fig_quad.add_scatter(
        x=focal_row["net_migration_rate"], y=focal_row["talent_concentration"],
        mode="markers+text", text=[focal_state], textposition="top right",
        marker=dict(size=18, color="gold", line=dict(width=2, color="black")),
        showlegend=False, name=focal_state,
    )
    fig_quad.update_layout(legend_title="Policy Segment")
    st.plotly_chart(fig_quad, use_container_width=True)

    # Segment table
    st.markdown('<div class="section-header">State Segment Summary</div>', unsafe_allow_html=True)
    seg_summary = df.groupby("segment").agg(
        States=("state", "count"),
        Avg_Net_Rate=("net_migration_rate", "mean"),
        Avg_Concentration=("talent_concentration", "mean"),
    ).round(2).reset_index()
    seg_summary.columns = ["Segment", "# States", "Avg Net Rate (per 1k)", "Avg Talent Concentration (%)"]
    st.dataframe(seg_summary, use_container_width=True, hide_index=True)


#
# MODULE 2: TALENT FLOW
#
elif analysis_section == " Talent Flow: Inflow vs Outflow":
    st.header(" Talent Flow: Inflow vs. Outflow Analysis")
    st.markdown("""
    <div class="warn-box">
    <b> Important:</b> In-migration figures (B07009) reflect current-year arrivals. Out-migration figures (B07409)
    are based on prior-year residence — the best available ACS proxy for out-migration, but not a perfect mirror.
    Net figures should be interpreted directionally.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # Diverging bar: net migration rate
        st.markdown('<div class="section-header">Net Educated Migration Rate (per 1,000 residents 25+)</div>', unsafe_allow_html=True)
        df_div = df[["state", "net_migration_rate"]].sort_values("net_migration_rate")
        df_div["color"] = df_div["net_migration_rate"].apply(lambda x: "#c62828" if x < 0 else "#1565c0")
        fig_div = go.Figure(go.Bar(
            x=df_div["net_migration_rate"],
            y=df_div["state"],
            orientation="h",
            marker_color=df_div["color"],
            text=df_div["net_migration_rate"].round(2),
            textposition="outside",
        ))
        fig_div.add_vline(x=0, line_width=2, line_color="black")
        fig_div.update_layout(
            height=900, xaxis_title="Net Rate per 1,000",
            yaxis={"categoryorder": "total ascending"}, showlegend=False,
        )
        st.plotly_chart(fig_div, use_container_width=True)

    with col2:
        # Top gainers vs losers
        st.markdown('<div class="section-header">Top 10 Gainers vs. Top 10 Losers</div>', unsafe_allow_html=True)
        top10_gain = df.nlargest(10, "net_educated_migrants")[["state", "net_educated_migrants", "segment"]]
        top10_loss = df.nsmallest(10, "net_educated_migrants")[["state", "net_educated_migrants", "segment"]]
        combined = pd.concat([top10_gain, top10_loss]).sort_values("net_educated_migrants")
        combined["color"] = combined["net_educated_migrants"].apply(lambda x: "#c62828" if x < 0 else "#1565c0")

        fig_comb = go.Figure(go.Bar(
            x=combined["net_educated_migrants"],
            y=combined["state"],
            orientation="h",
            marker_color=combined["color"],
        ))
        fig_comb.add_vline(x=0, line_width=2, line_color="black")
        fig_comb.update_layout(
            height=500, xaxis_title="Net Educated Migrants (absolute)",
            yaxis={"categoryorder": "total ascending"}, showlegend=False,
        )
        st.plotly_chart(fig_comb, use_container_width=True)

        # Educated share of total migration
        st.markdown('<div class="section-header">Educated Share of Total Interstate Migration</div>', unsafe_allow_html=True)
        df_share = df[["state", "edu_share_of_inmig", "edu_share_of_outmig"]].dropna()
        df_share = df_share.sort_values("edu_share_of_inmig", ascending=False).head(20)
        df_share_melt = df_share.melt(id_vars="state", var_name="Direction", value_name="Share (%)")
        df_share_melt["Direction"] = df_share_melt["Direction"].map({
            "edu_share_of_inmig": "In-migration",
            "edu_share_of_outmig": "Out-migration (est.)",
        })
        fig_share = px.bar(
            df_share_melt, x="Share (%)", y="state", color="Direction",
            orientation="h", barmode="group",
            color_discrete_map={"In-migration": "#1565c0", "Out-migration (est.)": "#c62828"},
            title="Top 20 States: Educated Workers as % of All Interstate Movers",
            height=500,
        )
        fig_share.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_share, use_container_width=True)

    # Stacked comparison for degree type
    st.markdown('<div class="section-header">Inflow Composition: Bachelor\'s vs. Graduate Degree</div>', unsafe_allow_html=True)
    df_comp = df[["state", "interstate_in_bachelors", "interstate_in_graduate"]].sort_values(
        "interstate_in_bachelors", ascending=False
    ).head(30)
    df_comp_melt = df_comp.melt(id_vars="state", var_name="Degree", value_name="Count")
    df_comp_melt["Degree"] = df_comp_melt["Degree"].map({
        "interstate_in_bachelors": "Bachelor's",
        "interstate_in_graduate": "Graduate/Professional",
    })
    fig_stack = px.bar(
        df_comp_melt, x="Count", y="state", color="Degree", orientation="h",
        barmode="relative",
        color_discrete_map={"Bachelor's": "#1565c0", "Graduate/Professional": "#0d47a1"},
        title="In-Migration Composition by Degree Level (Top 30 States by Volume)",
        height=700,
    )
    fig_stack.update_layout(barnorm="percent", yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_stack, use_container_width=True)


#
# MODULE 3: INCOME & TALENT
#
elif analysis_section == " Income & Talent Correlation":
    st.header(" Income, Earnings & Talent Attraction")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">Earnings vs. Net Migration Rate</div>', unsafe_allow_html=True)
        st.caption("States offering higher wages for educated workers may attract more talent.")
        df_earn = df.dropna(subset=["median_earnings_bachelors", "net_migration_rate"])
        fig_earn = px.scatter(
            df_earn,
            x="median_earnings_bachelors",
            y="net_migration_rate",
            size="stock_educated_total",
            color="segment",
            hover_name="state",
            color_discrete_map={
                " Talent Hub": "#1565c0", " Rising Gainer": "#2e7d32",
                " At-Risk Retainer": "#f57c00", " Brain Drain Risk": "#c62828",
            },
            labels={
                "median_earnings_bachelors": "Median Earnings: Bachelor's Degree ($)",
                "net_migration_rate": "Net Educated Migration Rate (per 1k)",
            },
            title="Bachelor's Earnings vs. Net Educated Migration Rate",
            trendline="ols",
            height=450,
        )
        # Highlight focal state
        focal_row = df_earn[df_earn["state"] == focal_state]
        if not focal_row.empty:
            fig_earn.add_scatter(
                x=focal_row["median_earnings_bachelors"], y=focal_row["net_migration_rate"],
                mode="markers+text", text=[focal_state], textposition="top right",
                marker=dict(size=16, color="gold", line=dict(width=2, color="black")),
                showlegend=False,
            )
        st.plotly_chart(fig_earn, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Graduate Earnings vs. In-Migration Rate</div>', unsafe_allow_html=True)
        df_grad_earn = df.dropna(subset=["median_earnings_graduate", "edu_inmig_rate"])
        fig_grad = px.scatter(
            df_grad_earn,
            x="median_earnings_graduate",
            y="edu_inmig_rate",
            size="stock_educated_total",
            color="segment",
            hover_name="state",
            color_discrete_map={
                " Talent Hub": "#1565c0", " Rising Gainer": "#2e7d32",
                " At-Risk Retainer": "#f57c00", " Brain Drain Risk": "#c62828",
            },
            labels={
                "median_earnings_graduate": "Median Earnings: Graduate Degree ($)",
                "edu_inmig_rate": "Educated In-Migration Rate (per 1k)",
            },
            title="Graduate Earnings vs. Educated In-Migration Rate",
            trendline="ols",
            height=450,
        )
        focal_row2 = df_grad_earn[df_grad_earn["state"] == focal_state]
        if not focal_row2.empty:
            fig_grad.add_scatter(
                x=focal_row2["median_earnings_graduate"], y=focal_row2["edu_inmig_rate"],
                mode="markers+text", text=[focal_state], textposition="top right",
                marker=dict(size=16, color="gold", line=dict(width=2, color="black")),
                showlegend=False,
            )
        st.plotly_chart(fig_grad, use_container_width=True)

    # Earnings ranking bar chart
    st.markdown('<div class="section-header">Median Earnings by Education Level — State Comparison</div>', unsafe_allow_html=True)
    df_earn_long = df[["state", "median_earnings_bachelors", "median_earnings_graduate", "median_earnings_total"]]\
        .dropna().sort_values("median_earnings_bachelors", ascending=False)
    df_earn_melt = df_earn_long.melt(id_vars="state", var_name="Level", value_name="Median Earnings ($)")
    df_earn_melt["Level"] = df_earn_melt["Level"].map({
        "median_earnings_bachelors": "Bachelor's",
        "median_earnings_graduate": "Graduate/Professional",
        "median_earnings_total": "All Education Levels",
    })
    fig_rank_earn = px.bar(
        df_earn_melt,
        x="Median Earnings ($)", y="state", color="Level", orientation="h",
        barmode="group",
        color_discrete_map={
            "Bachelor's": "#1565c0",
            "Graduate/Professional": "#0d47a1",
            "All Education Levels": "#78909c",
        },
        title="Median Earnings by Education Level (Pop. 25+)",
        height=900,
    )
    fig_rank_earn.update_layout(yaxis={"categoryorder": "array", "categoryarray": df_earn_long["state"].tolist()})
    st.plotly_chart(fig_rank_earn, use_container_width=True)


#
# MODULE 4: EDUCATION STOCK
#
elif analysis_section == " Education Stock & Concentration":
    st.header(" Education Stock & Talent Concentration")
    st.caption("Understanding the existing talent pool is critical before interpreting migration flows.")

    col1, col2 = st.columns(2)

    with col1:
        # Talent concentration ranking
        st.markdown('<div class="section-header">Talent Concentration Index (% Pop 25+ with BA or Higher)</div>', unsafe_allow_html=True)
        df_conc = df[["state", "talent_concentration", "segment"]].sort_values("talent_concentration", ascending=False)
        fig_conc = px.bar(
            df_conc,
            x="talent_concentration", y="state", color="segment", orientation="h",
            color_discrete_map={
                " Talent Hub": "#1565c0", " Rising Gainer": "#2e7d32",
                " At-Risk Retainer": "#f57c00", " Brain Drain Risk": "#c62828",
            },
            labels={"talent_concentration": "% Population 25+ with BA+", "state": ""},
            title="Talent Concentration by State",
            height=900,
        )
        fig_conc.update_layout(yaxis={"categoryorder": "total ascending"})
        nat_avg = df["talent_concentration"].mean()
        fig_conc.add_vline(x=nat_avg, line_dash="dash", line_color="black",
                           annotation_text=f"National avg: {nat_avg:.1f}%",
                           annotation_position="top right")
        st.plotly_chart(fig_conc, use_container_width=True)

    with col2:
        # Graduate degree composition heatmap (stock)
        st.markdown('<div class="section-header">Graduate Degree Composition of Education Stock</div>', unsafe_allow_html=True)
        df_deg = df[["state", "stock_bachelors", "stock_masters", "stock_professional", "stock_doctorate"]]\
            .sort_values("stock_bachelors", ascending=False).head(30)
        df_deg_melt = df_deg.melt(id_vars="state", var_name="Degree", value_name="Count")
        df_deg_melt["Degree"] = df_deg_melt["Degree"].map({
            "stock_bachelors": "Bachelor's",
            "stock_masters": "Master's",
            "stock_professional": "Professional",
            "stock_doctorate": "Doctorate",
        })
        fig_deg = px.bar(
            df_deg_melt, x="Count", y="state", color="Degree", orientation="h",
            barmode="relative",
            color_discrete_sequence=px.colors.sequential.Blues_r,
            title="Education Stock Composition (Top 30 States)",
            height=700,
        )
        fig_deg.update_layout(barnorm="percent", yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_deg, use_container_width=True)

    # Migration as % of stock — key brain drain indicator
    st.markdown('<div class="section-header">Out-Migration as % of Educated Stock — The Brain Drain Signal</div>', unsafe_allow_html=True)
    st.caption("States where a large share of their educated workers are leaving face structural talent erosion.")
    df_drain = df[["state", "inmig_pct_of_stock", "outmig_pct_of_stock", "segment"]].dropna().sort_values("outmig_pct_of_stock", ascending=False)
    df_drain_melt = df_drain.melt(id_vars=["state", "segment"], var_name="Direction", value_name="% of Stock")
    df_drain_melt["Direction"] = df_drain_melt["Direction"].map({
        "inmig_pct_of_stock": "In-Migration % of Stock",
        "outmig_pct_of_stock": "Out-Migration % of Stock",
    })
    fig_stock_pct = px.scatter(
        df_drain.dropna(),
        x="inmig_pct_of_stock", y="outmig_pct_of_stock",
        color="segment",
        size="stock_educated_total",
        hover_name="state",
        color_discrete_map={
            " Talent Hub": "#1565c0", " Rising Gainer": "#2e7d32",
            " At-Risk Retainer": "#f57c00", " Brain Drain Risk": "#c62828",
        },
        labels={
            "inmig_pct_of_stock": "Educated In-Migrants as % of Stock",
            "outmig_pct_of_stock": "Educated Out-Migrants as % of Stock",
        },
        title="In-Migration vs. Out-Migration as % of Educated Stock",
        height=500,
    )
    fig_stock_pct.add_shape(type="line", x0=0, y0=0, x1=15, y1=15, line=dict(color="gray", dash="dash"))
    fig_stock_pct.add_annotation(x=12, y=13, text="Equilibrium line", showarrow=False,
                                 font=dict(color="gray", size=10))
    focal_row3 = df_drain[df_drain["state"] == focal_state]
    if not focal_row3.empty:
        fig_stock_pct.add_scatter(
            x=focal_row3["inmig_pct_of_stock"], y=focal_row3["outmig_pct_of_stock"],
            mode="markers+text", text=[focal_state], textposition="top right",
            marker=dict(size=16, color="gold", line=dict(width=2, color="black")),
            showlegend=False,
        )
    st.plotly_chart(fig_stock_pct, use_container_width=True)


#
# MODULE 5: STATE COMPARISON
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
# MODULE 6: GOVERNOR'S BRIEFING
#
elif analysis_section == " Governor's Briefing":
    st.header(f" Governor's Briefing: {focal_state}")
    st.markdown("*A narrative policy summary for executive decision-making.*")

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

    # Policy narrative box
    net = focal["net_educated_migrants"]
    conc = focal["talent_concentration"]
    nat_net = df["net_educated_migrants"].median()
    nat_conc = df["talent_concentration"].median()

    if net > nat_net and conc > nat_conc:
        narrative = f"""**{focal_state} is a Talent Hub.** The state both attracts significant educated talent from other states
        AND maintains a high concentration of degree holders. This is a position of strength. Policy priority should focus on
        **retaining this advantage** through housing affordability, quality-of-life investments, and advanced industry development."""
    elif net > nat_net and conc <= nat_conc:
        narrative = f"""**{focal_state} is a Rising Gainer.** In-migration is above national median, indicating growing attractiveness,
        but the base talent concentration remains below the national average. This is a promising trend. Policy should focus on
        **deepening the talent pipeline** — growing higher education capacity and converting in-migrants into permanent residents."""
    elif net <= nat_net and conc > nat_conc:
        narrative = f"""**{focal_state} is an At-Risk Retainer.** The state has a strong existing talent pool but is experiencing
        below-median net migration — suggesting talent is leaving faster than new talent arrives. This is the classic "brain drain" warning.
        Policy must urgently address **competitive wages, remote work infrastructure, and cost-of-living** to stem outflows."""
    else:
        narrative = f"""**{focal_state} faces Brain Drain Risk.** Both net migration and talent concentration are below national medians.
        The state is losing educated workers and not replacing them at sufficient rates. Without intervention, this creates a compounding
        disadvantage. Immediate priorities should include **targeted talent attraction incentives, rural broadband, and industry diversification.**"""

    st.markdown(f'<div class="policy-box"><h4> Executive Policy Summary</h4><p>{narrative}</p></div>', unsafe_allow_html=True)

    # 3-panel story: stock → flow → outcome
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="section-header">1. Talent Stock</div>', unsafe_allow_html=True)
        df["Highlight"] = df["state"].apply(lambda s: focal_state if s == focal_state else "Other States")
        fig_s1 = px.bar(
            df, x="stock_educated_total", y="state", color="Highlight",
            color_discrete_map={focal_state: "#f9a825", "Other States": "#cfd8dc"},
            orientation="h",
            labels={"stock_educated_total": "Total BA+ Holders", "state": ""},
            title="Educated Population Stock",
            height=750,
        )
        fig_s1.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(fig_s1, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">2. Educated Migration Flow</div>', unsafe_allow_html=True)
        fig_s2 = px.scatter(
            df, x="interstate_in_educated", y="interstate_out_educated",
            color="Highlight",
            color_discrete_map={focal_state: "#f9a825", "Other States": "#90a4ae"},
            size="stock_educated_total",
            hover_name="state",
            labels={"interstate_in_educated": "In-Migrants", "interstate_out_educated": "Out-Migrants (est.)"},
            title="In vs. Out Migration Volume",
            height=750,
        )
        fig_s2.add_shape(type="line", x0=0, y0=0,
                         x1=df["interstate_in_educated"].max(), y1=df["interstate_in_educated"].max(),
                         line=dict(color="gray", dash="dash"))
        st.plotly_chart(fig_s2, use_container_width=True)

    with col3:
        st.markdown('<div class="section-header">3. Policy Outcome Position</div>', unsafe_allow_html=True)
        fig_s3 = px.scatter(
            df, x="net_migration_rate", y="talent_concentration",
            color="Highlight",
            color_discrete_map={focal_state: "#f9a825", "Other States": "#90a4ae"},
            size="stock_educated_total",
            hover_name="state",
            labels={"net_migration_rate": "Net Migration Rate", "talent_concentration": "Talent Concentration (%)"},
            title="Net Rate vs. Concentration",
            height=750,
        )
        fig_s3.add_hline(y=df["talent_concentration"].median(), line_dash="dash", line_color="gray", opacity=0.5)
        fig_s3.add_vline(x=df["net_migration_rate"].median(), line_dash="dash", line_color="gray", opacity=0.5)
        st.plotly_chart(fig_s3, use_container_width=True)

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
# MODULE 7: METHODOLOGY
#
elif analysis_section == " Methodology & Limitations":
    st.header(" Methodology & Data Limitations")

    st.markdown("""
    <div class="policy-box">
    <h4> Data Sources (All ACS 5-Year Estimates)</h4>
    <ul>
    <li><b>B07009</b> — Geographical Mobility by Educational Attainment (current residence). Used for in-migration counts.
        Interstate in-migrants = "Moved from different state" rows (_025E total, _029E bachelor's, _030E graduate/professional).</li>
    <li><b>B07409</b> — Geographical Mobility by Educational Attainment (residence 1 year ago). Used as a <em>proxy</em> for out-migration.
        This captures people whose prior-year address was in a given state and who moved away.</li>
    <li><b>B15003</b> — Educational Attainment for Population 25+. Provides the "stock" of degree holders as the denominator
        for concentration and drain calculations (_022E BA, _023E MA, _024E Professional, _025E Doctorate).</li>
    <li><b>B20004</b> — Median Earnings by Sex by Educational Attainment. Used for wage competitiveness analysis
        (_005E bachelor's earnings, _006E graduate earnings).</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="warn-box">
    <h4> Critical Interpretation Flags</h4>
    <p><b>1. In-migration vs. Net Migration:</b> B07009 captures people who <em>arrived</em> in a state from another state.
    It does not capture who left. B07409 (prior-year residence) is the best proxy for out-migration but is not a perfect
    complement — methodological differences exist between the two tables. Net figures are directional estimates.</p>

    <p><b>2. Age limitations:</b> ACS B07009/B07409 cover population 25+ but do not isolate the 22–35 "young professional"
    cohort specifically. The app analyzes the full 25+ educated population, which includes older degree holders.</p>

    <p><b>3. Safe terminology:</b> Use "educated in-migration" and "estimated net migration." Avoid asserting "brain drain"
    as a confirmed fact — this analysis identifies <em>risk indicators</em>, not causation.</p>

    <p><b>4. Earnings (B20004):</b> These are median earnings for workers with earnings — not all residents.
    They reflect current state market conditions and may understate remote-worker income if that worker moved for lifestyle reasons.</p>

    <p><b>5. ACS 5-Year estimates:</b> These are period estimates (e.g., 2018–2022), not single-year snapshots.
    They are best for structural comparisons, not tracking year-over-year changes.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="policy-box">
    <h4> Computed Metrics</h4>
    <ul>
    <li><b>Net Educated Migration</b> = Interstate In-Migrants (educated) − Interstate Out-Migrants est. (educated)</li>
    <li><b>Migration Rates</b> = (migrants / pop_25plus) × 1,000</li>
    <li><b>Talent Concentration</b> = (BA+ stock / total pop 25+) × 100</li>
    <li><b>Migration as % of Stock</b> = (migrants / BA+ stock) × 100 — key brain drain signal</li>
    <li><b>Educated Share of Migration</b> = (educated migrants / all migrants) × 100 — quality signal</li>
    <li><b>Policy Segments</b>: Based on median splits of net migration rate and talent concentration:
        Talent Hub (high/high), Rising Gainer (high/low), At-Risk Retainer (low/high), Brain Drain Risk (low/low)</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
