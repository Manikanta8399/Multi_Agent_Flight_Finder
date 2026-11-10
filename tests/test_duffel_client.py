import requests
import pytest

from src.duffel_client import search_duffel_flights


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError("HTTP request failed")

    def json(self):
        return self.payload


def test_search_duffel_flights_sends_search_and_normalizes_offer(monkeypatch):
    captured_request = {}
    payload = {
        "data": {
            "offers": [
                {
                    "total_amount": "123.45",
                    "total_currency": "EUR",
                    "slices": [
                        {
                            "duration": "PT2H30M",
                            "segments": [
                                {
                                    "departing_at": "2027-09-21T10:00:00",
                                    "arriving_at": "2027-09-21T11:00:00",
                                    "operating_carrier": {"name": "Example Air"},
                                },
                                {
                                    "departing_at": "2027-09-21T11:30:00",
                                    "arriving_at": "2027-09-21T12:30:00",
                                    "operating_carrier": {"name": "Connector Airways"},
                                },
                            ],
                        }
                    ],
                }
            ]
        }
    }

    def fake_post(url, **kwargs):
        captured_request["url"] = url
        captured_request.update(kwargs)
        return FakeResponse(payload)

    monkeypatch.setattr("src.duffel_client.requests.post", fake_post)

    result = search_duffel_flights(
        "San Francisco", "New York", "2027-09-21", "test-access-token"
    )

    assert result["success"] is True
    assert captured_request["url"] == "https://api.duffel.com/air/offer_requests"
    assert captured_request["headers"]["Authorization"] == "Bearer test-access-token"
    assert captured_request["headers"]["Duffel-Version"] == "v2"
    assert captured_request["json"]["data"]["slices"][0]["origin"] == "SFO"
    assert captured_request["json"]["data"]["slices"][0]["destination"] == "NYC"
    assert result["results"] == [
        {
            "airline": "Example Air / Connector Airways",
            "origin": "San Francisco",
            "destination": "New York",
            "date": "2027-09-21",
            "departure_time": "2027-09-21T10:00:00",
            "arrival_time": "2027-09-21T12:30:00",
            "duration": "2h 30m",
            "stops": 1,
            "price": 123.45,
            "currency": "EUR",
        }
    ]


def test_search_duffel_flights_supports_adults_cabin_and_return_slice(monkeypatch):
    captured_request = {}
    payload = {
        "data": {
            "offers": [
                {
                    "total_amount": "900.00",
                    "total_currency": "USD",
                    "slices": [
                        {
                            "duration": "PT5H",
                            "segments": [
                                {
                                    "departing_at": "2027-09-21T08:00:00",
                                    "arriving_at": "2027-09-21T13:00:00",
                                    "operating_carrier": {"name": "Outbound Air"},
                                }
                            ],
                        },
                        {
                            "duration": "PT5H30M",
                            "segments": [
                                {
                                    "departing_at": "2027-09-28T09:00:00",
                                    "arriving_at": "2027-09-28T14:30:00",
                                    "operating_carrier": {"name": "Return Air"},
                                }
                            ],
                        },
                    ],
                }
            ]
        }
    }

    def fake_post(url, **kwargs):
        captured_request.update(kwargs)
        return FakeResponse(payload)

    monkeypatch.setattr("src.duffel_client.requests.post", fake_post)

    result = search_duffel_flights(
        "SFO",
        "NYC",
        "2027-09-21",
        "test-token",
        passenger_count=2,
        cabin_class="business",
        return_date="2027-09-28",
    )

    request_data = captured_request["json"]["data"]
    assert result["success"] is True
    assert len(request_data["passengers"]) == 2
    assert request_data["cabin_class"] == "business"
    assert request_data["slices"] == [
        {"origin": "SFO", "destination": "NYC", "departure_date": "2027-09-21"},
        {"origin": "NYC", "destination": "SFO", "departure_date": "2027-09-28"},
    ]
    assert result["results"][0]["return_departure_time"] == "2027-09-28T09:00:00"
    assert result["results"][0]["return_arrival_time"] == "2027-09-28T14:30:00"
    assert result["results"][0]["return_duration"] == "5h 30m"


@pytest.mark.parametrize("passenger_count", [0, 10])
def test_search_duffel_flights_rejects_invalid_passenger_count_without_request(
    monkeypatch, passenger_count
):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Invalid search options must not be sent to Duffel")

    monkeypatch.setattr("src.duffel_client.requests.post", fail_if_called)

    result = search_duffel_flights(
        "SFO", "NYC", "2027-09-21", "test-token", passenger_count=passenger_count
    )

    assert result["success"] is False
    assert "1 and 9" in result["message"]


def test_search_duffel_flights_rejects_return_date_before_departure_without_request(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Invalid return date must not be sent to Duffel")

    monkeypatch.setattr("src.duffel_client.requests.post", fail_if_called)

    result = search_duffel_flights(
        "SFO",
        "NYC",
        "2027-09-21",
        "test-token",
        return_date="2027-09-20",
    )

    assert result["success"] is False
    assert result["message"] == "Return date must be after the departure date."


def test_search_duffel_flights_rejects_empty_return_date_without_request(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Invalid return date must not be sent to Duffel")

    monkeypatch.setattr("src.duffel_client.requests.post", fail_if_called)

    result = search_duffel_flights(
        "SFO",
        "NYC",
        "2027-09-21",
        "test-token",
        return_date="",
    )

    assert result["success"] is False
    assert result["message"] == "Return date must use YYYY-MM-DD format."


def test_search_duffel_flights_returns_safe_error_without_access_token(monkeypatch):
    monkeypatch.delenv("DUFFEL_ACCESS_TOKEN", raising=False)

    result = search_duffel_flights("San Francisco", "New York", "2027-09-21", "")

    assert result["success"] is False
    assert result["results"] == []
    assert "DUFFEL_ACCESS_TOKEN" in result["message"]


def test_search_duffel_flights_does_not_send_example_placeholder_token(monkeypatch):
    monkeypatch.delenv("DUFFEL_ACCESS_TOKEN", raising=False)

    result = search_duffel_flights(
        "San Francisco",
        "New York",
        "2027-09-21",
        "replace_with_your_test_token",
    )

    assert result["success"] is False
    assert "DUFFEL_ACCESS_TOKEN" in result["message"]


def test_search_duffel_flights_reports_no_offers(monkeypatch):
    monkeypatch.setattr(
        "src.duffel_client.requests.post",
        lambda *args, **kwargs: FakeResponse({"data": {"offers": []}}),
    )

    result = search_duffel_flights("San Francisco", "New York", "2027-09-21", "token")

    assert result["success"] is False
    assert result["results"] == []
    assert result["message"] == "No flights found for this route and date."


def test_search_duffel_flights_handles_malformed_response(monkeypatch):
    monkeypatch.setattr(
        "src.duffel_client.requests.post",
        lambda *args, **kwargs: FakeResponse({"data": "unexpected"}),
    )

    result = search_duffel_flights("SFO", "NYC", "2027-09-21", "token")

    assert result["success"] is False
    assert result["results"] == []
    assert "unexpected response" in result["message"].lower()


def test_search_duffel_flights_rejects_unmapped_city_without_request(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("No request should be sent for an unmapped city")

    monkeypatch.setattr("src.duffel_client.requests.post", fail_if_called)

    result = search_duffel_flights("Atlantis", "New York", "2027-09-21", "token")

    assert result["success"] is False
    assert result["results"] == []
    assert "IATA" in result["message"]
    assert result["missing_fields"] == ["origin"]


def test_search_duffel_flights_returns_safe_error_on_timeout(monkeypatch):
    def timeout(*args, **kwargs):
        raise requests.Timeout("request timed out")

    monkeypatch.setattr("src.duffel_client.requests.post", timeout)

    result = search_duffel_flights("SFO", "NYC", "2027-09-21", "token")

    assert result["success"] is False
    assert result["results"] == []
    assert "search failed" in result["message"].lower()