# AI Flight Finder

This project is a beginner-friendly flight finder built in small steps.

## Goal

The app accepts a natural-language flight question, extracts the important details, and prepares the request for a real flight-search integration.

## Current milestone

The app can parse example queries such as:

- "Find flights from San Francisco to New York on September 21, 2027."

It validates missing fields and asks for more details if needed.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Learning focus

- Understand natural-language input
- Extract origin, destination, and date
- Validate missing data before searching
- Prepare the app for a real flight API later
