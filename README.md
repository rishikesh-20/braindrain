# Brain Drain Intelligence Platform

**Team 2 — Economic Policy Advisors to the Governor**

An interactive Streamlit dashboard for analyzing interstate migration of educated workers across all 50 U.S. states, built on U.S. Census Bureau American Community Survey (ACS) 5-Year Estimates.

---

## What It Does

This tool helps policymakers understand where educated workers are moving, which states are gaining or losing talent, and how a state's wage competitiveness, education stock, young-adult mobility, and renter cost burden relate to migration patterns. It pulls live data from seven ACS tables and computes normalized metrics to support evidence-based policy decisions.

---

## Analysis Modules

| Module | Description |
|---|---|
| **Executive Dashboard** | KPI cards, net migration choropleth, consistency matrix, manual peer benchmarking |
| **Talent Flow** | Diverging bar of net educated migration rate, educated share of migration, degree composition |
| **Income & Talent Correlation** | Wage competitiveness vs migration outcome scatter plots |
| **Education Stock & Concentration** | Talent concentration ranking, rent-burden ranking, brain drain signal (out-migration as % of stock) |
| **Young Talent + Affordability Risk** | Young-adult migration analysis (ages 25-34), rent-burden scatter/ranking, diagnostic table |
| **State Comparison Tool** | Side-by-side metrics table and normalized radar chart for any two states |
| **Governor's Briefing** | Data-based executive summary for the selected state |
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
| **B07001** | Geographic Mobility by Age (current residence) | Young in-migration ages 25-29 and 30-34 |
| **B07401** | Geographic Mobility by Age (residence 1 year ago) | Young out-migration proxy ages 25-29 and 30-34 |
| **B25070** | Gross Rent as a Percentage of Household Income | Rent-burden bins used to compute share of renters spending 30%+ of income on housing |

---

## Computed Metrics

- **Net Educated Migration** = Educated in-migrants − Educated out-migrants (est.)
- **Educated Net Migration Rate** = (net educated migrants / pop 25+) × 1,000
- **Young Net Migration Rate** = ((young in-migrants − young out-migrants) / pop 25-34) × 1,000
- **Talent Concentration** = (BA+ stock / total pop 25+) × 100
- **Rent-Burden Rate (30%+)** = share of renter households spending 30%+ of income on housing
- **Migration as % of Stock** = (migrants / BA+ stock) × 100 — a core brain-drain signal
- **Policy Segments** — states classified by median splits of net migration rate and talent concentration:
  - **Talent Hub** — high net migration, high concentration
  - **Rising Gainer** — high net migration, low concentration
  - **At-Risk Retainer** — low net migration, high concentration
  - **Brain Drain Risk** — low net migration, low concentration

All dashboard views are currently presented in **normalized per-1,000 terms** where applicable.

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
.venv/bin/streamlit run app.py
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
altair
```

---

## Important Methodology Notes

- **B07409 is a proxy**, not a perfect mirror of B07009. Net migration figures are directional estimates, not exact counts.
- **Age coverage**: Educated-worker migration uses 25+ tables, while the young-talent module uses age bins 25-29 and 30-34 from separate ACS tables. This improves age specificity but does not isolate degree status within the young-only view.
- **Earnings (B20004)**: Reflect workers with earnings only — may understate income for remote workers who relocated for lifestyle reasons.
- **Affordability proxy**: B25070 measures renter cost burden only. It does not capture owner housing costs or the full cost of living.
- **ACS 5-Year estimates** are period averages (e.g., 2018–2022), not single-year snapshots. Best for structural comparisons.
- **Peer benchmarking**: Comparison states are selected manually in the app; peers are not auto-generated by a predictive model.

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
