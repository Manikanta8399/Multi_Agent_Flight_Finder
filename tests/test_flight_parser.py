from src.flight_parser import parse_flight_query


def test_parse_flight_query_extracts_details():
    result = parse_flight_query("Find flights from San Francisco to New York on September 21, 2027.")

    assert result["origin"] == "San Francisco"
    assert result["destination"] == "New York"
    assert result["date"] == "2027-09-21"


def test_parse_flight_query_requires_missing_destination():
    result = parse_flight_query("Find flights from San Francisco on September 21, 2027.")

    assert result["success"] is False
    assert result["origin"] == "San Francisco"
    assert result["date"] == "2027-09-21"
    assert result["missing_fields"] == ["destination"]


def test_parse_flight_query_requires_missing_origin():
    result = parse_flight_query("Find flights to New York on September 21, 2027.")

    assert result["success"] is False
    assert result["destination"] == "New York"
    assert result["date"] == "2027-09-21"
    assert result["missing_fields"] == ["origin"]
    assert "origin" in result["message"].lower()


def test_parse_flight_query_handles_missing_year():
    result = parse_flight_query("Find flights from San Francisco to New York")

    assert result["success"] is False
    assert "date" in result["missing_fields"]
