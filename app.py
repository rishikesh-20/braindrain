import streamlit as st
import pandas as pd
from census import Census
from us import states
import plotly.express as px

st.set_page_config(
    page_title="Brain Drain Analysis",
    layout="wide"
)

st.title("Team 2: The 'Brain Drain' Analysts")
st.write("**Role:** Economic Policy Advisors to the Governor")
st.write("**Task:** Analyzing educated interstate migration to identify talent attraction vs. flight.")

# Data Loading
API_KEY = st.secrets["CENSUS_API_KEY"]

@st.cache_data
def load_acs_data():
    c = Census(API_KEY)

    variables = (
        "NAME",
        "B07009_001E",
        "B07009_013E",
        "B07009_016E"
    )

    data = c.acs5.state(
        variables,
        Census.ALL
    )

    df = pd.DataFrame(data)

    df = df.drop(columns=["state"], errors="ignore")  # Drop existing 'state' column to prevent duplication

    df = df.rename(columns={
        "NAME": "state",
        "B07009_001E": "population_25_plus",
        "B07009_013E": "bachelors_migrants",
        "B07009_016E": "graduate_migrants"
    })

    cols = [
        "population_25_plus",
        "bachelors_migrants",
        "graduate_migrants"
    ]

    df[cols] = df[cols].apply(
        pd.to_numeric,
        errors="coerce"
    )

    df["educated_migrants"] = (
        df["bachelors_migrants"] +
        df["graduate_migrants"]
    )

    df["educated_migration_rate"] = (
        df["educated_migrants"] /
        df["population_25_plus"]
    ) * 1000

    df = df.dropna(subset=["population_25_plus", "educated_migrants", "educated_migration_rate"])

    return df

df = load_acs_data()

# Navigation
analysis_section = st.sidebar.radio(
    "Select Analysis Module",
    [
        "1. Talent Attraction Landscape",
        "2. Migration Patterns & Correlations",
        "3. Competitive Benchmarking",
        "4. State Profile: The Governor's Briefing",
        "5. Methodology & Limitations"
    ]
)

if analysis_section == "1. Talent Attraction Landscape":
    st.header("Executive Summary: The Talent Attraction Landscape")
    st.markdown("Where is the educated talent actually going?")
    
    # 1. The Magnet Metric
    st.subheader("The Magnet Metric: Who Attracts the Most Talent?")
    st.markdown("Identifies absolute leaders in talent attraction volume.")
    fig1 = px.bar(
        df, 
        x="educated_migrants", 
        y="state", 
        color="educated_migration_rate", 
        orientation='h',
        title="Total Educated Migrants by State",
        labels={"educated_migrants": "Total Educated Migrants", "state": "State", "educated_migration_rate": "Rate per 1k"},
        height=800
    )
    fig1.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig1, use_container_width=True)

    # 2. The Efficiency Index
    st.subheader("The Efficiency Index: High Impact per Capita")
    st.markdown("Highlights states where in-migration is a significant driver relative to population size.")
    fig2 = px.scatter(
        df, 
        x="educated_migration_rate", 
        y="state", 
        size="population_25_plus",
        title="Educated Migration Rate vs State (Size = Pop)",
        labels={"educated_migration_rate": "Educated Migrants per 1k Residents", "state": "State"},
        height=800
    )
    fig2.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig2, use_container_width=True)

    # 3. The Degree Mix (Category Control)
    st.subheader("The Degree Mix: Bachelor's vs. Graduate")
    st.markdown("Reveals the quality/specialization of the incoming talent pool.")
    
    df_melted = df.melt(
        id_vars=["state"], 
        value_vars=["bachelors_migrants", "graduate_migrants"],
        var_name="degree_type", 
        value_name="count"
    )
    
    fig3 = px.scatter(
        df_melted, 
        x="count", 
        y="state", 
        color="degree_type", 
        log_x=True,
        title="Migrant Count by Degree Type (Log Scale)",
        labels={"count": "Migrant Count", "state": "State", "degree_type": "Degree Level"},
        height=800
    )
    fig3.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig3, use_container_width=True)

    # 4. The Opportunity Matrix
    st.subheader("The Opportunity Matrix: Volume vs. Rate")
    st.markdown("Segments states into Established Hubs, Sleeping Giants, Niche Magnets, and Stagnant areas.")
    fig4 = px.scatter(
        df, 
        x="educated_migrants", 
        y="educated_migration_rate", 
        log_x=True, 
        hover_name="state",
        title="Volume vs Rate Analysis",
        labels={"educated_migrants": "Total Educated Migrants (Log)", "educated_migration_rate": "Rate per 1k"}
    )
    st.plotly_chart(fig4, use_container_width=True)

elif analysis_section == "2. Migration Patterns & Correlations":
    st.header("Deep Dive: Migration Patterns & Correlations")
    st.markdown("Analytical views on distribution, correlation, and composition.")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Ranking (Bar)")
        # Top 10 States
        fig_rank = px.bar(
            df.sort_values("educated_migration_rate", ascending=False).head(10),
            x="educated_migration_rate",
            y="state",
            color="educated_migrants",
            orientation='h',
            title="Top 10 States by Rate"
        )
        fig_rank.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_rank, use_container_width=True)

        st.subheader("Distribution (Strip)")
        fig_strip = px.strip(
            df, 
            x="educated_migration_rate", 
            y="state", 
            color="educated_migration_rate", 
            orientation='h',
            title="Distribution of Migration Rates",
            height=800
        )
        st.plotly_chart(fig_strip, use_container_width=True)

    with col2:
        st.subheader("Correlation (Scatter)")
        fig_corr = px.scatter(
            df, 
            x="population_25_plus", 
            y="educated_migrants", 
            log_x=True, 
            log_y=True,
            color="educated_migration_rate",
            hover_name="state",
            title="Population vs Migrants (Log-Log)"
        )
        st.plotly_chart(fig_corr, use_container_width=True)

        st.subheader("Composition (Heatmap)")
        # Integrated Efficiency Heatmap (Magnitude Control)
        # Using a density heatmap or a bar chart styled as a strip can work. 
        # Making a 1D Heatmap using px.imshow or px.bar
        fig_heat = px.density_heatmap(
            df, 
            x="state", 
            y="educated_migration_rate", 
            z="educated_migration_rate", 
            histfunc="avg",
            title="Efficiency Heatmap"
        )
        # Simplest way to get the "strip" look with Plotly is actually a bar chart with color mapped
        fig_heat_bar = px.bar(
            df.sort_values("educated_migration_rate", ascending=False),
            x="state",
            y="educated_migration_rate",
            color="educated_migration_rate",
            color_continuous_scale="Viridis",
            title="Efficiency Heatmap (Bar Representation)",
            height=800
        )
        st.plotly_chart(fig_heat_bar, use_container_width=True)

elif analysis_section == "3. Competitive Benchmarking":
    st.header("Competitive Benchmarking")
    
    st.subheader("Ranking: Who is #1?")
    st.markdown("Ordered Bar Chart to show rank.")
    fig_comp_rank = px.bar(
        df, 
        x="educated_migration_rate", 
        y="state", 
        orientation='h',
        title="State Ranking by Rate",
        height=800
    )
    fig_comp_rank.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_comp_rank, use_container_width=True)

    st.subheader("Deviation: Winners vs Laggards (Direction)")
    st.markdown("Diverging bar chart showing performance vs national mean.")
    
    mean_rate = df["educated_migration_rate"].mean()
    df["deviation"] = df["educated_migration_rate"] - mean_rate
    
    fig_div = px.bar(
        df, 
        x="deviation", 
        y="state", 
        color="deviation", 
        orientation='h',
        color_continuous_scale="RdBu",
        title="Deviation from National Mean",
        height=800
    )
    fig_div.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_div, use_container_width=True)

    st.subheader("Composition: Talent Makeup")
    st.markdown("100% Stacked Bar (Bachelor's vs Graduate).")
    df_melted_comp = df.melt(
        id_vars=["state"], 
        value_vars=["bachelors_migrants", "graduate_migrants"], 
        var_name="degree", 
        value_name="count"
    )
    # Plotly handles normalization with 'barnorm' or we can let it stack naturaly. 
    # For 100% stack, we use groupnorm='percent' if available or just stack. 
    # Creating a stacked bar.
    fig_comp = px.bar(
        df_melted_comp, 
        x="count", 
        y="state", 
        color="degree", 
        orientation='h', 
        barmode='relative',
        title="Talent Composition"
    )
    # To make it 100% stacked, we actually need to normalize the values first or strictly use groupnorm (available in recent plotly versions)
    # Ideally for 100% stacked:
    fig_comp = px.bar(
        df_melted_comp, 
        x="count", 
        y="state", 
        color="degree", 
        orientation='h',
        title="Talent Composition (100% Stacked)",
        height=800
    )
    # Correct way to stack 100% horizontally is to normalize the x-axis via barnorm on layout
    fig_comp.update_layout(barnorm='percent')
    fig_comp.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_comp, use_container_width=True)

elif analysis_section == "4. State Profile: The Governor's Briefing":
    st.header("Governor's Briefing: State Profile")
    
    state_filter = st.selectbox("Highlight State", df["state"].unique(), index=0)
    
    # Create a color mapping column
    df["Highlight"] = df["state"].apply(lambda x: "Selected" if x == state_filter else "Other")
    color_map = {"Selected": "orange", "Other": "lightgrey"}

    st.subheader("1. The Context: Baseline Talent Pool")
    st.markdown("We start by identifying our existing workforce size.")
    fig_story1 = px.bar(
        df, 
        x="population_25_plus", 
        y="state", 
        color="Highlight", 
        color_discrete_map=color_map,
        orientation='h',
        title="Baseline Population",
        height=800
    )
    fig_story1.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    st.plotly_chart(fig_story1, use_container_width=True)

    st.subheader("2. The Action: Raw Attraction Volume")
    st.markdown(f"Next, we look at how many educated people {state_filter} actually attracted.")
    fig_story2 = px.scatter(
        df, 
        x="educated_migrants", 
        y="state", 
        size="educated_migrants", 
        color="Highlight", 
        color_discrete_map=color_map,
        title="Educated In-Migrants Volume",
        height=800
    )
    fig_story2.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    st.plotly_chart(fig_story2, use_container_width=True)

    st.subheader("3. The Impact: Normalized Efficiency")
    st.markdown(f"Finally, we normalize by population to see efficiency. Is {state_filter} punching above its weight?")
    # Using a bar chart or strip plot for efficiency
    fig_story3 = px.bar(
        df, 
        x="educated_migration_rate", 
        y="state", 
        color="Highlight", 
        color_discrete_map=color_map,
        orientation='h',
        title="Migration Efficiency (Rate per 1k)",
        height=800
    )
    fig_story3.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    st.plotly_chart(fig_story3, use_container_width=True)

elif analysis_section == "5. Methodology & Limitations":
    st.header("Methodology & Data Limitations")
    st.warning("IMPORTANT: Interpretation Flags")
    st.markdown("""
    ### 🚩 "Brain Drain" vs "Brain Gain"
    *   **LIMITATION**: This dataset only shows **IN-MIGRATION** (people arriving).
    *   **MISSING**: It does NOT show OUT-MIGRATION (people leaving).
    *   **CONCLUSION**: We can measure "Attraction" (Gain), but we CANNOT measure true "Brain Drain" (Net Loss) with this table alone.
    
    ### ✅ Safe Terminology
    *   Use: "Gross In-Migration", "Talent Attraction", "Educated Newcomers"
    *   Avoid: "Net Migration", "Brain Drain" (unless referring to the *risk* of not attracting enough to replace outflows, which is speculative).
    """)
