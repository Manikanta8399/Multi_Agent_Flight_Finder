import json

from src.agents.flight_search_tool import FlightSearchTool


def test_flight_search_tool_uses_only_validated_request_and_calls_once(monkeypatch):
    captured = {}
    result = {"success": True, "results": [{"airline": "Example Air"}]}
    callback_calls = []

    def fake_search_flights(origin, destination, date, **options):
        captured["request"] = (origin, destination, date, options)
        return result

    monkeypatch.setattr("src.agents.flight_search_tool.search_flights", fake_search_flights)
    tool = FlightSearchTool(
        expected_origin="San Francisco",
        expected_destination="New York",
        expected_departure_date="2027-09-21",
        passenger_count=2,
        cabin_class="business",
        return_date="2027-09-28",
        on_search_complete=lambda: callback_calls.append("complete"),
    )
    arguments = {
        "origin": "San Francisco",
        "destination": "New York",
        "departure_date": "2027-09-21",
        "passenger_count": 2,
        "cabin_class": "business",
        "return_date": "2027-09-28",
    }

    first_output = json.loads(tool._run(**arguments))
    second_output = json.loads(tool._run(**arguments))

    assert first_output == result
    assert second_output["success"] is False
    assert "one flight search" in second_output["message"]
    assert captured["request"] == (
        "San Francisco",
        "New York",
        "2027-09-21",
        {
            "passenger_count": 2,
            "cabin_class": "business",
            "return_date": "2027-09-28",
        },
    )
    assert callback_calls == ["complete"]


def test_flight_search_tool_rejects_model_changed_arguments(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("Changed arguments must not reach the provider")

    monkeypatch.setattr("src.agents.flight_search_tool.search_flights", fail_if_called)
    tool = FlightSearchTool(
        expected_origin="San Francisco",
        expected_destination="New York",
        expected_departure_date="2027-09-21",
    )

    output = json.loads(
        tool._run(
            origin="San Francisco",
            destination="Boston",
            departure_date="2027-09-21",
        )
    )

    assert output["success"] is False
    assert "differ from the validated request" in output["message"]
    assert tool.result["destination"] == "New York"
