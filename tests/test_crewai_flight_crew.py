import json
from types import SimpleNamespace

from src.agents.crewai_flight_crew import CrewAIFlightCrew


def test_crewai_crew_runs_search_tool_then_returns_agent_summary(monkeypatch):
    captured = {}
    flights = {
        "success": True,
        "results": [
            {
                "airline": "Example Air",
                "price": 123,
                "currency": "USD",
                "duration": "2h 30m",
                "stops": 0,
            }
        ],
    }

    class FakeLLM:
        def __init__(self, **kwargs):
            captured["llm"] = kwargs

    class FakeAgent:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            captured.setdefault("agents", []).append(self)

    class FakeTask:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            captured.setdefault("tasks", []).append(self)

    class FakeCrew:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            captured["crew"] = self

        def kickoff(self, inputs):
            search_tool = self.kwargs["agents"][0].kwargs["tools"][0]
            search_values = json.loads(inputs["search_context"])
            search_tool._run(**search_values)
            return SimpleNamespace(raw="Example Air is the available nonstop option.")

    monkeypatch.setattr("src.agents.crewai_flight_crew.LLM", FakeLLM)
    monkeypatch.setattr("src.agents.crewai_flight_crew.Agent", FakeAgent)
    monkeypatch.setattr("src.agents.crewai_flight_crew.Task", FakeTask)
    monkeypatch.setattr("src.agents.crewai_flight_crew.Crew", FakeCrew)
    monkeypatch.setattr("src.agents.crewai_flight_crew.Process", SimpleNamespace(sequential="sequential"))
    monkeypatch.setattr("src.agents.flight_search_tool.search_flights", lambda *args, **kwargs: flights)
    progress = []

    result = CrewAIFlightCrew().run(
        {
            "origin": "San Francisco",
            "destination": "New York",
            "date": "2027-09-21",
        },
        search_options={"passenger_count": 1, "cabin_class": "economy", "return_date": None},
        on_progress=progress.append,
    )

    assert result["flights"] is flights
    assert result["summary"]["cheapest"] == flights["results"][0]
    assert result["summary"]["summary"] == "Example Air is the available nonstop option."
    assert len(captured["agents"]) == 2
    assert len(captured["tasks"]) == 2
    assert captured["crew"].kwargs["process"] == "sequential"
    assert progress == ["summarizing"]


def test_crewai_crew_fails_safely_when_agent_skips_search_tool(monkeypatch):
    class FakeLLM:
        def __init__(self, **kwargs):
            pass

    class FakeAgent:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeTask:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeCrew:
        def __init__(self, **kwargs):
            pass

        def kickoff(self, inputs):
            return SimpleNamespace(raw="No tool was called.")

    monkeypatch.setattr("src.agents.crewai_flight_crew.LLM", FakeLLM)
    monkeypatch.setattr("src.agents.crewai_flight_crew.Agent", FakeAgent)
    monkeypatch.setattr("src.agents.crewai_flight_crew.Task", FakeTask)
    monkeypatch.setattr("src.agents.crewai_flight_crew.Crew", FakeCrew)
    monkeypatch.setattr("src.agents.crewai_flight_crew.Process", SimpleNamespace(sequential="sequential"))

    result = CrewAIFlightCrew().run(
        {
            "origin": "San Francisco",
            "destination": "New York",
            "date": "2027-09-21",
        }
    )

    assert result["flights"]["success"] is False
    assert result["flights"]["results"] == []
    assert "did not call" in result["flights"]["message"]
