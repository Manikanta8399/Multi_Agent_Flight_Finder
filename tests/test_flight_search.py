from src.flight_search import search_flights


def test_search_flights_returns_matching_results(monkeypatch):
    monkeypatch.setenv("FLIGHT_SEARCH_PROVIDER", "sample")
    result = search_flights("San Francisco", "New York", "2027-09-21")
    flights = result["results"]

    assert result["success"] is True
    assert len(flights) >= 3
    assert all(f["origin"] == "San Francisco" for f in flights)
    assert all(f["destination"] == "New York" for f in flights)
    assert all(f["date"] == "2027-09-21" for f in flights)


def test_search_flights_reports_when_no_sample_flights_match(monkeypatch):
    monkeypatch.setenv("FLIGHT_SEARCH_PROVIDER", "sample")
    result = search_flights("Seattle", "Boston", "2027-09-21")

    assert result["success"] is False
    assert result["results"] == []
    assert result["missing_fields"] == []
    assert result["message"] == "No flights found for this route and date."


def test_search_flights_rejects_missing_origin(monkeypatch):
    monkeypatch.setenv("FLIGHT_SEARCH_PROVIDER", "sample")
    result = search_flights("", "New York", "2027-09-21")

    assert result["success"] is False
    assert "origin" in result["missing_fields"]


def test_search_flights_rejects_missing_destination(monkeypatch):
    monkeypatch.setenv("FLIGHT_SEARCH_PROVIDER", "sample")
    result = search_flights("San Francisco", "", "2027-09-21")

    assert result["success"] is False
    assert "destination" in result["missing_fields"]


def test_search_flights_requires_token_when_duffel_provider_is_selected(monkeypatch):
    monkeypatch.setenv("FLIGHT_SEARCH_PROVIDER", "duffel")
    monkeypatch.delenv("DUFFEL_ACCESS_TOKEN", raising=False)

    result = search_flights("San Francisco", "New York", "2027-09-21")

    assert result["success"] is False
    assert "DUFFEL_ACCESS_TOKEN" in result["message"]


def test_search_flights_routes_to_duffel_when_selected(monkeypatch):
    expected_result = {"success": True, "results": [{"airline": "Example Air"}]}
    monkeypatch.setenv("FLIGHT_SEARCH_PROVIDER", "duffel")
    monkeypatch.setenv("DUFFEL_ACCESS_TOKEN", "test-token")
    monkeypatch.setattr(
        "src.flight_search.search_duffel_flights",
        lambda origin, destination, date, **options: expected_result,
    )

    result = search_flights("San Francisco", "New York", "2027-09-21")

    assert result is expected_result


def test_search_flights_passes_options_to_duffel(monkeypatch):
    captured_options = {}
    monkeypatch.setenv("FLIGHT_SEARCH_PROVIDER", "duffel")
    monkeypatch.setattr(
        "src.flight_search.search_duffel_flights",
        lambda origin, destination, date, **options: captured_options.update(options)
        or {"success": True, "results": []},
    )

    search_flights(
        "San Francisco",
        "New York",
        "2027-09-21",
        passenger_count=2,
        cabin_class="business",
        return_date="2027-09-28",
    )

    assert captured_options == {
        "passenger_count": 2,
        "cabin_class": "business",
        "return_date": "2027-09-28",
    }


def test_sample_search_rejects_options_it_cannot_model(monkeypatch):
    monkeypatch.setenv("FLIGHT_SEARCH_PROVIDER", "sample")

    result = search_flights(
        "San Francisco",
        "New York",
        "2027-09-21",
        passenger_count=2,
    )

    assert result["success"] is False
    assert "Sample mode supports" in result["message"]
