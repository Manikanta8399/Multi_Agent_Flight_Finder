from src.agents.request_worker import (
    RequestUnderstandingWorkerAgent,
    build_clarified_query,
    build_search_correction_request,
)


def test_request_worker_uses_deterministic_parser_for_supported_query(monkeypatch):
    def fail_if_called(prompt):
        raise AssertionError("Ollama should not be called for a supported query")

    monkeypatch.setattr("src.agents.request_worker.generate_summary", fail_if_called)

    result = RequestUnderstandingWorkerAgent().run(
        "Find flights from San Francisco to New York on September 21, 2027."
    )

    assert result["success"] is True
    assert result["origin"] == "San Francisco"
    assert result["destination"] == "New York"
    assert result["date"] == "2027-09-21"


def test_request_worker_uses_ollama_for_unfamiliar_wording(monkeypatch):
    monkeypatch.setattr(
        "src.agents.request_worker.generate_summary",
        lambda prompt: '{"origin":"San Francisco","destination":"New York","date":"2027-09-21"}',
    )

    result = RequestUnderstandingWorkerAgent().run(
        "Please find a flight San Francisco to New York for September 21, 2027."
    )

    assert result["success"] is True
    assert result["origin"] == "San Francisco"
    assert result["destination"] == "New York"
    assert result["date"] == "2027-09-21"


def test_request_worker_cleans_descriptive_city_name(monkeypatch):
    monkeypatch.setattr(
        "src.agents.request_worker.generate_summary",
        lambda prompt: '{"origin":"San Francisco","destination":"New York","date":"2027-09-21"}',
    )

    result = RequestUnderstandingWorkerAgent().run(
        "Find flights from San Francisco to the greatest city New York on September 21, 2027."
    )

    assert result["success"] is True
    assert result["origin"] == "San Francisco"
    assert result["destination"] == "New York"
    assert result["date"] == "2027-09-21"


def test_request_worker_reports_missing_fields_from_ai_response(monkeypatch):
    monkeypatch.setattr(
        "src.agents.request_worker.generate_summary",
        lambda prompt: '{"origin":null,"destination":"New York","date":"2027-09-21"}',
    )

    result = RequestUnderstandingWorkerAgent().run(
        "Please find a flight to New York for September 21, 2027."
    )

    assert result["success"] is False
    assert result["destination"] == "New York"
    assert result["date"] == "2027-09-21"
    assert result["missing_fields"] == ["origin"]


def test_request_worker_falls_back_when_ai_response_is_invalid(monkeypatch):
    monkeypatch.setattr(
        "src.agents.request_worker.generate_summary",
        lambda prompt: "I cannot parse this request.",
    )
    query = "Please find a flight to New York for September 21, 2027."

    result = RequestUnderstandingWorkerAgent().run(query)

    assert result["success"] is False
    assert result["query"] == query


def test_build_clarified_query_combines_user_answer_with_known_details():
    parsed = {
        "origin": None,
        "destination": "New York",
        "date": "2027-09-21",
    }

    query = build_clarified_query(parsed, {"origin": " San Francisco "})

    assert query == "Find flights from San Francisco to New York on 2027-09-21"


def test_build_clarified_query_waits_when_any_required_answer_is_blank():
    parsed = {"origin": None, "destination": "New York", "date": "2027-09-21"}

    query = build_clarified_query(parsed, {"origin": "  "})

    assert query is None


def test_search_correction_request_asks_for_unmapped_city_only():
    parsed = {
        "origin": "Atlantis",
        "destination": "New York",
        "date": "2027-09-21",
        "query": "Find flights from Atlantis to New York on September 21, 2027.",
    }
    search_result = {
        "success": False,
        "missing_fields": ["origin"],
        "message": "I could not map a city to an IATA code.",
    }

    correction = build_search_correction_request(parsed, search_result)

    assert correction["origin"] is None
    assert correction["destination"] == "New York"
    assert correction["date"] == "2027-09-21"
    assert correction["missing_fields"] == ["origin"]


def test_search_correction_request_allows_changes_when_no_flights_match():
    parsed = {
        "origin": "San Francisco",
        "destination": "New York",
        "date": "2027-09-21",
    }
    search_result = {
        "success": False,
        "missing_fields": [],
        "message": "No flights found for this route and date.",
    }

    correction = build_search_correction_request(parsed, search_result)

    assert correction["missing_fields"] == ["origin", "destination", "date"]
    assert correction["origin"] is None
    assert correction["destination"] is None
    assert correction["date"] is None
    assert "Try changing" in correction["message"]


def test_search_correction_request_ignores_provider_configuration_errors():
    parsed = {
        "origin": "San Francisco",
        "destination": "New York",
        "date": "2027-09-21",
    }
    search_result = {
        "success": False,
        "missing_fields": [],
        "message": "Duffel is selected, but DUFFEL_ACCESS_TOKEN is not configured in .env.",
    }

    assert build_search_correction_request(parsed, search_result) is None