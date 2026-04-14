# Brain Drain Intelligence Platform

Interactive Streamlit dashboard for analyzing interstate migration of educated workers across all 50 U.S. states using live U.S. Census Bureau ACS 5-Year Estimates data.

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

The app now includes grounded Gemini features on the Executive Dashboard and Governor's Briefing pages:

- AI governor briefing generation
- AI chart explanations
- Ask-the-data chat

These features are intentionally constrained to use only the Census-derived metrics already computed by the app plus the in-app methodology notes. They do not fetch outside data.

## Verification Checklist

- `uv sync` completes successfully
- `uv run streamlit run app.py` starts the app
- Gemini AI controls appear only when `GEMINI_API_KEY` is present
- North Carolina KPI values match the current deployed app
- Choropleth map renders correctly
- State comparison still works
- Governor briefing values match
- No missing dependency errors appear at runtime
