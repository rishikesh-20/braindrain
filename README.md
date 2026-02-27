# Brain Drain Intelligence Platform

**Team 2 — Economic Policy Advisors to the Governor**

An interactive Streamlit dashboard for analyzing interstate migration of educated workers across all 50 U.S. states, built on U.S. Census Bureau American Community Survey (ACS) 5-Year Estimates.

---

## What It Does

This tool helps policymakers understand where educated workers are moving, which states are gaining or losing talent, and how a state's wage competitiveness and education stock relate to migration patterns. It pulls live data from four ACS tables and computes advanced metrics to support evidence-based policy decisions.

---

## Analysis Modules

| Module | Description |
|---|---|
| **Executive Dashboard** | KPI cards, national talent positioning quadrant map, top gainers/losers |
| **Talent Flow** | Diverging bar chart of net migration, in vs. out scatter, degree composition |
| **Income & Talent Correlation** | Scatter plots correlating median earnings with migration rates |
| **Education Stock & Concentration** | Talent concentration ranking, brain drain signal (out-migration as % of stock) |
| **State Comparison Tool** | Side-by-side metrics table and normalized radar chart for any two states |
| **Governor's Briefing** | Auto-generated narrative policy summary with 3-panel story chart |
| **Methodology & Limitations** | Data sources, variable codes, interpretation flags, computed metric definitions |

---

## Data Sources

All data pulled live from the U.S. Census Bureau ACS 5-Year Estimates API.

| Table | Description | Key Variables |
|---|---|---|
| **B07009** | Geographic Mobility by Educational Attainment (current residence) | `_025E` total interstate in-movers, `_029E` bachelor's, `_030E` graduate |
| **B07409** | Geographic Mobility by Educational Attainment (residence 1 year ago) | Out-migration proxy — same variable structure as B07009 |
| **B15003** | Educational Attainment for Population 25+ | `_022E` BA, `_023E` MA, `_024E` professional, `_025E` doctorate |
| **B20004** | Median Earnings by Educational Attainment | `_005E` bachelor's earnings, `_006E` graduate earnings |

---

## Computed Metrics

- **Net Educated Migration** = Educated in-migrants − Educated out-migrants (est.)
- **Migration Rate** = (migrants / pop 25+) × 1,000
- **Talent Concentration** = (BA+ stock / total pop 25+) × 100
- **Migration as % of Stock** = (migrants / BA+ stock) × 100 — the core brain drain signal
- **Policy Segments** — states classified by median splits of net migration rate and talent concentration:
  - **Talent Hub** — high net migration, high concentration
  - **Rising Gainer** — high net migration, low concentration
  - **At-Risk Retainer** — low net migration, high concentration
  - **Brain Drain Risk** — low net migration, low concentration

---

## Setup & Running Locally

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate      # Mac/Linux
.venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 3. Add your Census API key

Get a free key at [api.census.gov/data/key_signup.html](https://api.census.gov/data/key_signup.html).

Create the Streamlit secrets file:

```bash
mkdir -p .streamlit
echo 'CENSUS_API_KEY = "your_key_here"' > .streamlit/secrets.toml
```

### 4. Run the app

```bash
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501).

---

## Deploying to Streamlit Cloud

1. Push the repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo
3. In the app settings, add your Census API key under **Secrets**:
   ```
   CENSUS_API_KEY = "your_key_here"
   ```
4. Deploy — the app rebuilds automatically on every `git push`

---

## Requirements

```
streamlit
pandas
census
us
plotly
statsmodels
```

---

## Important Methodology Notes

- **B07409 is a proxy**, not a perfect mirror of B07009. Net migration figures are directional estimates, not exact counts.
- **Age coverage**: Tables cover population 25+ and cannot isolate the 22–35 young professional cohort specifically.
- **Earnings (B20004)**: Reflect workers with earnings only — may understate income for remote workers who relocated for lifestyle reasons.
- **ACS 5-Year estimates** are period averages (e.g., 2018–2022), not single-year snapshots. Best for structural comparisons.

---

## Project Structure

```
.
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── .streamlit/
    └── secrets.toml        # Census API key (not committed to git)
```

---

*Built for the Governor's Economic Policy Advisory Team using U.S. Census Bureau public data.*
