from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_app_shows_correction_form_when_search_cannot_map_origin(monkeypatch):
    parsed = {
        "success": True,
        "origin": "Atlantis",
        "destination": "New York",
        "date": "2027-09-21",
        "missing_fields": [],
        "query": "Find flights from Atlantis to New York on September 21, 2027.",
    }

    class FakeMasterAgent:
        def run(self, query, on_progress=None, search_options=None):
            return {
                "success": False,
                "stage": "search",
                "parsed": parsed,
                "flights": {
                    "success": False,
                    "missing_fields": ["origin"],
                    "message": "I could not map a city to an IATA code.",
                    "results": [],
                },
                "summary": None,
            }

    monkeypatch.setattr(
        "src.agents.master_agent.FlightFinderMasterAgent", FakeMasterAgent
    )
    app = AppTest.from_file(str(APP_PATH)).run()
    app.text_area(key="flight_request_text").set_value(
        "Find flights from Atlantis to New York on September 21, 2027."
    ).run()
    app.button[0].click().run()

    assert len(app.text_input) == 1
    assert "flying from" in app.text_input[0].label.lower()
    assert any("could not map" in item.value.lower() for item in app.info)
