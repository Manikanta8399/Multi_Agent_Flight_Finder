import re
from datetime import datetime


DATE_FORMATS = (
    "%B %d, %Y",
    "%b %d, %Y",
    "%B %d %Y",
    "%b %d %Y",
    "%Y-%m-%d",
)


def _parse_date(raw_date: str):
    if not raw_date:
        return None

    cleaned = raw_date.strip().rstrip(".")
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def _extract_value(query: str, keyword: str, next_keywords=None):
    next_keywords = next_keywords or []
    stop_pattern = "|".join(next_keywords) if next_keywords else ""

    if stop_pattern:
        pattern = rf"\b{keyword}\b\s+(?P<value>.+?)(?=\s+\b(?:{stop_pattern})\b|$)"
    else:
        pattern = rf"\b{keyword}\b\s+(?P<value>.+)$"

    match = re.search(pattern, query, re.IGNORECASE)
    if not match:
        return None

    value = (match.group("value") or "").strip().rstrip(".")
    return value or None


def _build_missing_fields_message(missing_fields):
    if not missing_fields:
        return "All required flight details are present."

    labels = {
        "origin": "origin city",
        "destination": "destination city",
        "date": "travel date",
    }

    readable_fields = [labels.get(field, field) for field in missing_fields]

    if len(readable_fields) == 1:
        return f"I am missing the {readable_fields[0]}."

    if len(readable_fields) == 2:
        return f"I am missing the {readable_fields[0]} and {readable_fields[1]}."

    return (
        f"I am missing the {', '.join(readable_fields[:-1])}, "
        f"and {readable_fields[-1]}."
    )


def parse_flight_query(query: str):
    if not query or not query.strip():
        missing_fields = ["origin", "destination", "date"]
        return {
            "success": False,
            "origin": None,
            "destination": None,
            "date": None,
            "missing_fields": missing_fields,
            "message": _build_missing_fields_message(missing_fields),
            "query": query,
        }

    origin = _extract_value(query, "from", ["to", "on"])
    destination = _extract_value(query, "to", ["on"])
    raw_date = _extract_value(query, "on") or ""

    parsed_date = _parse_date(raw_date)
    missing_fields = []

    if not origin:
        missing_fields.append("origin")
    if not destination:
        missing_fields.append("destination")
    if not parsed_date:
        missing_fields.append("date")

    return {
        "success": not missing_fields,
        "origin": origin,
        "destination": destination,
        "date": parsed_date,
        "missing_fields": missing_fields,
        "message": _build_missing_fields_message(missing_fields),
        "query": query,
    }
