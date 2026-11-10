from src.flight_summary import summarize_flights


def test_summarize_flights_uses_fallback_when_no_results():
    result = summarize_flights([])

    assert result["cheapest"] is None
    assert result["fastest"] is None
    assert result["best_choice"] is None
    assert "No flights available" in result["summary"]
