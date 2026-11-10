import json

from src.llm_client import generate_summary


def build_recommendation_cards(summary):
    if not summary or not summary.get("best_choice"):
        return {}

    cheapest = summary.get("cheapest")
    fastest = summary.get("fastest")
    best_choice = summary.get("best_choice")

    return {
        "cheapest": f"{cheapest['airline']} (${cheapest['price']})",
        "fastest": f"{fastest['airline']} ({fastest['duration']})",
        "best_choice": f"{best_choice['airline']} (${best_choice['price']})",
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


def summarize_flights(flights):
    if not flights:
        return {
            "cheapest": None,
            "fastest": None,
            "best_choice": None,
            "summary": "No flights available for this route.",
        }

    cheapest = min(flights, key=lambda f: f["price"])
    fastest = min(flights, key=lambda f: _parse_duration_to_minutes(f["duration"]))
    best_choice = cheapest

    flight_data = json.dumps(flights, indent=2)
    prompt = (
        "You are a travel assistant. Compare the flights below and answer in 2 short sentences. "
        "State the cheapest option, the fastest option, and the best overall choice. "
        "Keep the tone clear and helpful for a traveler.\n\nFlights:\n"
        f"{flight_data}"
    )

    ai_summary = generate_summary(prompt)

    if not ai_summary:
        ai_summary = (
            f"Cheapest option: {cheapest['airline']} at ${cheapest['price']}. "
            f"Fastest option: {fastest['airline']} in {fastest['duration']}. "
            f"Best overall value: {best_choice['airline']} at ${best_choice['price']}."
        )

    return {
        "cheapest": cheapest,
        "fastest": fastest,
        "best_choice": best_choice,
        "summary": ai_summary,
    }
