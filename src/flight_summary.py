import json

from src.llm_client import generate_summary


def _format_price(flight):
    currency = flight.get("currency", "USD")
    return f"{currency} {flight['price']:,.2f}"


def build_recommendation_cards(summary):
    if not summary or not summary.get("best_choice"):
        return {}

    cheapest = summary.get("cheapest")
    fastest = summary.get("fastest")
    best_choice = summary.get("best_choice")

    return {
        "cheapest": f"{cheapest['airline']} ({_format_price(cheapest)})",
        "fastest": f"{fastest['airline']} ({fastest['duration']})",
        "best_choice": f"{best_choice['airline']} ({_format_price(best_choice)})",
    }


def _parse_duration_to_minutes(duration_text):
    if not duration_text:
        return 0

    total_minutes = 0
    parts = duration_text.lower().replace(" ", "").split("h")

    if len(parts) > 1:
        total_minutes += int(parts[0]) * 60
        remaining = parts[1]
        if remaining.endswith("m"):
            total_minutes += int(remaining[:-1])
    else:
        if duration_text.lower().endswith("m"):
            total_minutes += int(duration_text.lower().replace("m", ""))

    return total_minutes


def _total_trip_duration_minutes(flight):
    total_minutes = _parse_duration_to_minutes(flight["duration"])
    return_duration = flight.get("return_duration")
    if return_duration:
        total_minutes += _parse_duration_to_minutes(return_duration)
    return total_minutes


def summarize_flights(flights, summary_text=None, use_llm=True):
    if not flights:
        return {
            "cheapest": None,
            "fastest": None,
            "best_choice": None,
            "summary": "No flights available for this route.",
        }

    cheapest = min(flights, key=lambda f: f["price"])
    fastest = min(flights, key=_total_trip_duration_minutes)
    best_choice = cheapest

    flight_data = json.dumps(flights, indent=2)
    prompt = (
        "You are a travel assistant. Compare the flights below and answer in 2 short sentences. "
        "State the cheapest option, the fastest option, and the best overall choice. "
        "Keep the tone clear and helpful for a traveler.\n\nFlights:\n"
        f"{flight_data}"
    )

    ai_summary = summary_text.strip() if isinstance(summary_text, str) else ""
    if not ai_summary and use_llm:
        ai_summary = generate_summary(prompt)

    if not ai_summary:
        ai_summary = (
            f"Cheapest option: {cheapest['airline']} at {_format_price(cheapest)}. "
            f"Fastest option: {fastest['airline']} in {fastest['duration']}. "
            f"Best overall value: {best_choice['airline']} at {_format_price(best_choice)}."
        )

    return {
        "cheapest": cheapest,
        "fastest": fastest,
        "best_choice": best_choice,
        "summary": ai_summary,
    }
