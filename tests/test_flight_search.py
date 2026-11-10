from src.flight_search import search_flights


def test_search_flights_returns_matching_results():
    result = search_flights("San Francisco", "New York", "2027-09-21")
    flights = result["results"]

    assert result["success"] is True
    assert len(flights) >= 3
    assert all(f["origin"] == "San Francisco" for f in flights)
    assert all(f["destination"] == "New York" for f in flights)
    assert all(f["date"] == "2027-09-21" for f in flights)


def test_search_flights_reports_when_no_sample_flights_match():
    result = search_flights("Seattle", "Boston", "2027-09-21")

    assert result["success"] is False
    assert result["results"] == []
    assert result["missing_fields"] == []
    assert result["message"] == "No flights found for this route and date."


def test_search_flights_rejects_missing_origin():
    result = search_flights("", "New York", "2027-09-21")

    assert result["success"] is False
    assert "origin" in result["missing_fields"]


def test_search_flights_rejects_missing_destination():
    result = search_flights("San Francisco", "", "2027-09-21")

    assert result["success"] is False
    assert "destination" in result["missing_fields"]
