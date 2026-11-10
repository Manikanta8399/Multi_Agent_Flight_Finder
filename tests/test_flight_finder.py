from src.agents.master_agent import FlightFinderMasterAgent


class StubWorker:
    def __init__(self, result, calls, name):
        self.result = result
        self.calls = calls
        self.name = name

    def run(self, value, search_options=None):
        self.calls.append((self.name, value))
        return self.result


def test_master_agent_coordinates_workers_in_order():
    query = "Find flights from San Francisco to New York on September 21, 2027."
    parsed = {
        "success": True,
        "origin": "San Francisco",
        "destination": "New York",
        "date": "2027-09-21",
        "missing_fields": [],
    }
    flights = {"success": True, "results": [{"airline": "Example Air"}]}
    summary = {"summary": "Example recommendation."}
    calls = []
    progress_stages = []
    master_agent = FlightFinderMasterAgent(
        request_worker=StubWorker(parsed, calls, "request"),
        search_worker=StubWorker(flights, calls, "search"),
        recommendation_worker=StubWorker(summary, calls, "recommendation"),
    )

    result = master_agent.run(query, on_progress=progress_stages.append)

    assert result["success"] is True
    assert result["stage"] == "complete"
    assert result["parsed"] is parsed
    assert result["flights"] is flights
    assert result["summary"] is summary
    assert [name for name, _ in calls] == ["request", "search", "recommendation"]
    assert progress_stages == ["validating", "searching", "summarizing"]


def test_master_agent_stops_when_request_is_incomplete():
    query = "Find flights to New York."
    parsed = {
        "success": False,
        "missing_fields": ["origin", "date"],
        "message": "I am missing the origin city and travel date.",
    }
    calls = []
    master_agent = FlightFinderMasterAgent(
        request_worker=StubWorker(parsed, calls, "request"),
        search_worker=StubWorker(None, calls, "search"),
        recommendation_worker=StubWorker(None, calls, "recommendation"),
    )

    result = master_agent.run(query)

    assert result["success"] is False
    assert result["stage"] == "validation"
    assert result["parsed"] is parsed
    assert result["flights"] is None
    assert result["summary"] is None
    assert [name for name, _ in calls] == ["request"]


def test_master_agent_stops_when_search_has_no_results():
    query = "Find flights from San Francisco to New York on September 21, 2027."
    parsed = {
        "success": True,
        "origin": "San Francisco",
        "destination": "New York",
        "date": "2027-09-21",
        "missing_fields": [],
    }
    flights = {
        "success": False,
        "results": [],
        "missing_fields": [],
        "message": "No flights found for this route and date.",
    }

    calls = []
    master_agent = FlightFinderMasterAgent(
        request_worker=StubWorker(parsed, calls, "request"),
        search_worker=StubWorker(flights, calls, "search"),
        recommendation_worker=StubWorker(None, calls, "recommendation"),
    )

    result = master_agent.run(query)

    assert result["success"] is False
    assert result["stage"] == "search"
    assert result["parsed"] is parsed
    assert result["flights"] is flights
    assert result["summary"] is None
    assert [name for name, _ in calls] == ["request", "search"]


def test_master_agent_delegates_default_search_and_summary_to_crewai():
    query = "Find flights from San Francisco to New York on September 21, 2027."
    parsed = {
        "success": True,
        "origin": "San Francisco",
        "destination": "New York",
        "date": "2027-09-21",
        "missing_fields": [],
    }
    flights = {"success": True, "results": [{"airline": "Example Air"}]}
    summary = {"summary": "CrewAI recommendation."}
    calls = []

    class StubCrew:
        def run(self, parsed_request, search_options=None, on_progress=None):
            calls.append((parsed_request, search_options))
            return {"flights": flights, "summary": summary}

    master_agent = FlightFinderMasterAgent(
        request_worker=StubWorker(parsed, [], "request"),
        crew_runner=StubCrew(),
    )

    result = master_agent.run(query, search_options={"passenger_count": 2})

    assert result["success"] is True
    assert result["flights"] is flights
    assert result["summary"] is summary
    assert calls == [(parsed, {"passenger_count": 2})]