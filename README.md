# Brain Drain Intelligence Platform

Interactive Streamlit dashboard for analyzing interstate migration of educated workers across all 50 U.S. states using live U.S. Census Bureau ACS 5-Year Estimates data.

App deployment URL: current deployed URL is not documented in this repo yet. Add the live `*.streamlit.app` URL here once deployment is verified with the new setup.

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
```

Get a free key at [api.census.gov/data/key_signup.html](https://api.census.gov/data/key_signup.html).

## Deployment Notes

This repo now defines dependencies in `pyproject.toml` and locks them in `uv.lock` for reproducible local installs.

## Verification Checklist

- `uv sync` completes successfully
- `uv run streamlit run app.py` starts the app
- North Carolina KPI values match the current deployed app
- Choropleth map renders correctly
- State comparison still works
- Governor briefing values match
- No missing dependency errors appear at runtime
