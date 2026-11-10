# AI Flight Finder

This project is a beginner-friendly flight finder built in small steps.

## Goal

The app accepts a natural-language flight question, extracts the important details, searches flights, and compares available options.

## Search modes

- **Sample mode** is the default and works without API credentials. Its demonstration data is only for San Francisco to New York on September 21, 2027.
- **Duffel mode** sends a flight offer request using your configured Duffel access token. Test-mode offers are for integration testing and do not guarantee real-world prices or availability.

To enable Duffel mode:

1. Create a test-mode API token in your Duffel account.
2. Copy `.env.example` to `.env`.
3. Set `FLIGHT_SEARCH_PROVIDER=duffel` and put your token in `DUFFEL_ACCESS_TOKEN` in `.env`.
4. Restart Streamlit and search again.

Never paste API tokens into source code, chat, or Git. `.env` is ignored by Git.

The app supports one-way and return searches, 1–9 adult travelers, and economy, premium economy, business, or first class in Duffel mode. For return trips, enter the return date in `YYYY-MM-DD` format. Sample mode only supports one adult, economy, one-way searches.

The natural-language request is capped at 500 characters and the return-date input at 10 characters. Dates and traveler counts are validated before any provider request is made.

Common city names are mapped to IATA city/airport codes in `src/duffel_client.py`; users can also enter a 3-letter IATA code such as `SFO` or `NYC`. The mapping is finite, not a complete worldwide airport directory.

If the request is missing a city or date, the app displays a follow-up form. It also asks the user to correct an unmapped city or revise the route/date when a search has no matching offers. When the user supplies updated details, it rebuilds the request and continues the search.

The provider integration uses Duffel's documented offer-request API and the existing `requests` dependency. Provider requests have a bounded timeout; automated tests use mocked responses and do not need a token or network access.

## Agent architecture

The app now uses CrewAI for the search-and-recommendation stage. The Python master in `src/agents/master_agent.py` first validates the request and returns to the UI for missing details. For a complete request, it starts a sequential CrewAI crew:

1. **Flight Search Agent** receives the validated trip and can call the bounded `search_flights` tool. The tool rejects changed trip details, allows one call per request, and routes only to the provider configured in `FLIGHT_SEARCH_PROVIDER`.
2. **Flight Recommendation Agent** receives the search task output and compares the available offers. Cheapest/fastest fields shown in the UI remain computed from provider data in Python; the agent writes the traveler-facing explanation.

The request-understanding worker still uses a deterministic parser first and calls local Ollama for ambiguous wording. Tool selection is intentionally constrained: the search agent only has the flight-search tool, and it cannot book or pay. The provider itself is selected by configuration, not by the LLM.

`CREWAI_MODEL` and `OLLAMA_BASE_URL` configure the local model connection. The current environment has `qwen2.5:7b`, which Ollama reports supports tools; set `CREWAI_MODEL=ollama/deepseek-r1:8b` only after that model is installed locally. This keeps the app runnable now while allowing the originally discussed DeepSeek-R1 option. `crewai[litellm]` is pinned in `requirements.txt` for CrewAI's Ollama integration.

Ticket purchasing is not implemented. Duffel test-mode offers do not guarantee live prices or availability; live fares require provider live-mode access. Never put payment details or API tokens in source code or chat.

API documentation: [Duffel Offer Requests](https://duffel.com/docs/api/offer-requests) and [Duffel key concepts](https://duffel.com/docs/api/overview/key-concepts).

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
- Keep the sample provider available for learning and offline testing
- Map natural-language city names to city/airport IATA codes
- Convert flight-provider offers into the app's common result format
