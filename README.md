Brain Drain Analysis

Educated Interstate Migration Using US Census ACS Data

Project Overview

This project analyzes interstate migration of educated adults in the United States using American Community Survey 5 Year data.

The objective is to evaluate whether states are experiencing brain drain or brain gain by measuring interstate movers with bachelor’s and graduate degrees.

The dashboard is built using Streamlit and pulls data directly from the US Census API.

Business Context

Role. Economic Policy Advisors to the Governor.

Policy concern. Educated young professionals may be leaving the state, reducing long term economic competitiveness.

This dashboard helps identify:
• Which states attract educated talent
• Which states lose educated talent
• Relative migration intensity across states

Data Source

Source. US Census Bureau
Dataset. American Community Survey 5 Year Estimates
Table. B07009
Table Name. Geographical Mobility by Educational Attainment in the Past Year

Key Variables Used:
• B07009_015E. Interstate movers with bachelor’s degree
• B07009_016E. Interstate movers with graduate or professional degree
• B07009_001E. Total population age 25 plus

Educated Migrants Definition:
Bachelor’s movers plus Graduate movers

Technical Stack

• Python
• Streamlit
• Census API
• Pandas
• Altair
• GitHub
• Streamlit Community Cloud

Features

• Live integration with US Census API
• Computation of educated migration counts
• Normalized migration rate per 1,000 residents
• Interactive state level visualization
• Policy oriented visual insights

How to Run Locally

Clone the repository

git clone https://github.com/rishikesh-20/braindrain.git

Install dependencies

pip install -r requirements.txt

Create a .streamlit folder

Inside it create secrets.toml

Add your Census API key

CENSUS_API_KEY = "your_api_key_here"

Run the app

streamlit run app.py

Deployment

The application is deployed using Streamlit Community Cloud.

Secrets are securely stored in the cloud environment.

Every push to the main branch triggers automatic redeployment.

AI Usage

Antigravity was used as a junior analyst to:
• Identify relevant ACS variables
• Validate table selection
• Suggest visualization designs

All calculations and interpretations were manually verified.

Policy Relevance

This dashboard supports data driven policy discussions on:
• Talent retention
• Workforce competitiveness
• Economic development strategy

It transforms raw Census data into actionable state level insights.
