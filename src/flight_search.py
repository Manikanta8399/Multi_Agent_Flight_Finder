import os

from src.duffel_client import search_duffel_flights
from src.flight_constants import NO_FLIGHTS_MESSAGE


SAMPLE_ORIGIN = "San Francisco"
SAMPLE_DESTINATION = "New York"
DEFAULT_SEARCH_PROVIDER = "sample"
DEFAULT_PASSENGER_COUNT = 1
DEFAULT_CABIN_CLASS = "economy"


def search_flights(
    origin,
    destination,
    date,
    passenger_count=DEFAULT_PASSENGER_COUNT,
    cabin_class=DEFAULT_CABIN_CLASS,
    return_date=None,
):
    missing_fields = []

    if not origin or not str(origin).strip():
        missing_fields.append("origin")
    if not destination or not str(destination).strip():
        missing_fields.append("destination")
    if not date or not str(date).strip():
        missing_fields.append("date")

    if missing_fields:
        return {
            "success": False,
            "origin": origin,
            "destination": destination,
            "date": date,
            "missing_fields": missing_fields,
            "results": [],
        }

    provider = os.getenv("FLIGHT_SEARCH_PROVIDER", DEFAULT_SEARCH_PROVIDER).strip().lower()
    if provider == "duffel":
        return search_duffel_flights(
            origin,
            destination,
            date,
            passenger_count=passenger_count,
            cabin_class=cabin_class,
            return_date=return_date,
        )
    if provider != "sample":
        return {
            "success": False,
            "origin": origin,
            "destination": destination,
            "date": date,
            "missing_fields": [],
            "message": "Unknown flight search provider. Set FLIGHT_SEARCH_PROVIDER to 'sample' or 'duffel'.",
            "results": [],
        }

    if (
        passenger_count != DEFAULT_PASSENGER_COUNT
        or cabin_class != DEFAULT_CABIN_CLASS
        or return_date is not None
    ):
        return {
            "success": False,
            "origin": origin,
            "destination": destination,
            "date": date,
            "missing_fields": [],
            "message": "Sample mode supports one adult, economy, one-way searches only. Select Duffel mode for these options.",
            "results": [],
        }

    sample_data = [
        {
            "airline": "Delta",
            "origin": SAMPLE_ORIGIN,
            "destination": SAMPLE_DESTINATION,
            "date": "2027-09-21",
            "departure_time": "08:15",
            "arrival_time": "15:40",
            "duration": "7h 25m",
            "stops": 0,
            "price": 319,
        },
        {
            "airline": "United",
            "origin": SAMPLE_ORIGIN,
            "destination": SAMPLE_DESTINATION,
            "date": "2027-09-21",
            "departure_time": "10:00",
            "arrival_time": "18:20",
            "duration": "8h 20m",
            "stops": 1,
            "price": 289,
        },
        {
            "airline": "JetBlue",
            "origin": SAMPLE_ORIGIN,
            "destination": SAMPLE_DESTINATION,
            "date": "2027-09-21",
            "departure_time": "12:45",
            "arrival_time": "21:10",
            "duration": "8h 25m",
            "stops": 0,
            "price": 349,
        },
        {
            "airline": "American",
            "origin": SAMPLE_ORIGIN,
            "destination": SAMPLE_DESTINATION,
            "date": "2027-09-21",
            "departure_time": "16:20",
            "arrival_time": "00:55",
            "duration": "8h 35m",
            "stops": 1,
            "price": 265,
        },
    ]

    filtered = [
        flight for flight in sample_data
        if flight["origin"] == origin and flight["destination"] == destination and flight["date"] == date
    ]

    sorted_flights = sorted(filtered, key=lambda item: item["price"])

    if not sorted_flights:
        return {
            "success": False,
            "origin": origin,
            "destination": destination,
            "date": date,
            "missing_fields": [],
            "message": NO_FLIGHTS_MESSAGE,
            "results": [],
        }

    return {
        "success": True,
        "origin": origin,
        "destination": destination,
        "date": date,
        "missing_fields": [],
        "results": sorted_flights,
    }
