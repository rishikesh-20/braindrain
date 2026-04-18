# Brain Drain Intelligence Platform

Interactive Streamlit dashboard for analyzing interstate migration of educated talent across all 50 U.S. states using U.S. Census Bureau ACS 5-Year Estimates data.

App deployment URL: [https://braindrain.streamlit.app/](https://braindrain.streamlit.app/)

## Local Setup with uv

```bash
git clone https://github.com/rishikesh-20/braindrain.git
cd braindrain
uv sync
uv run streamlit run app.py
```

The app expects a Census API key in `.streamlit/secrets.toml`:

```toml
CENSUS_API_KEY = "your_key_here"
GEMINI_API_KEY = "your_key_here"
```

Get a free key at [api.census.gov/data/key_signup.html](https://api.census.gov/data/key_signup.html).

If `GEMINI_API_KEY` is omitted, the dashboard still runs and the AI controls stay disabled.

## Deployment Notes

This repo now defines dependencies in `pyproject.toml` and locks them in `uv.lock` for reproducible local installs.

## Gemini Features

The app includes grounded Gemini features on the Executive Dashboard and Governor's Briefing pages:

- AI governor briefing generation
- AI chart explanations

These features are intentionally constrained to use only the Census-derived metrics already computed by the app. They do not fetch outside data, and the app falls back to deterministic summaries when AI is unavailable.

## App Modules

The current app is organized into five major sections:

- Executive Dashboard
- Young Talent + Affordability Risk
- State Comparison Tool
- Governor's Briefing
- Methodology & Limitations

The Executive Dashboard is the main decision-support view and includes KPI cards, a national positioning scatterplot, a geographic choropleth, peer benchmarking, and driver analysis views.

The Young Talent + Affordability Risk module adds a Phase 2 diagnostic layer focused on ages 25-34 mobility and rent burden.

The State Comparison Tool provides direct side-by-side benchmarking between two states through metric tables and normalized comparison views.

The Governor's Briefing module turns the selected state's metrics into an executive summary, an AI-generated briefing, and a normalized visual summary against U.S. medians.
