from src.flight_summary import build_recommendation_cards, summarize_flights


def test_summarize_flights_returns_best_options():
    flights = [
        {
            "airline": "Delta",
            "origin": "San Francisco",
            "destination": "New York",
            "date": "2027-09-21",
            "departure_time": "08:15",
            "arrival_time": "15:40",
            "duration": "7h 25m",
            "stops": 0,
            "price": 319,
        },
        {
            "airline": "American",
            "origin": "San Francisco",
            "destination": "New York",
            "date": "2027-09-21",
            "departure_time": "16:20",
            "arrival_time": "00:55",
            "duration": "8h 35m",
            "stops": 1,
            "price": 265,
        },
    ]

    summary = summarize_flights(flights)

    assert summary["cheapest"]["airline"] == "American"
    assert summary["fastest"]["airline"] == "Delta"
    assert "best_choice" in summary
    assert "summary" in summary


def test_build_recommendation_cards_returns_readable_choices():
    flights = [
        {
            "airline": "Delta",
            "origin": "San Francisco",
            "destination": "New York",
            "date": "2027-09-21",
            "departure_time": "08:15",
            "arrival_time": "15:40",
            "duration": "7h 25m",
            "stops": 0,
            "price": 319,
        },
        {
            "airline": "American",
            "origin": "San Francisco",
            "destination": "New York",
            "date": "2027-09-21",
            "departure_time": "16:20",
            "arrival_time": "00:55",
            "duration": "8h 35m",
            "stops": 1,
            "price": 265,
        },
    ]

    cards = build_recommendation_cards(summarize_flights(flights))

    assert cards["cheapest"].startswith("American")
    assert cards["fastest"].startswith("Delta")
    assert cards["best_choice"].startswith("American")


def test_summarize_flights_handles_empty_list():
    summary = summarize_flights([])

    assert summary["cheapest"] is None
    assert summary["fastest"] is None
    assert "No flights available" in summary["summary"]
