"""Worker responsible for searching the selected flight provider."""

from src.flight_search import search_flights


class FlightSearchWorkerAgent:
    def run(self, parsed_request, search_options=None):
        search_options = search_options or {}
        return search_flights(
            parsed_request["origin"],
            parsed_request["destination"],
            parsed_request["date"],
            passenger_count=search_options.get("passenger_count", 1),
            cabin_class=search_options.get("cabin_class", "economy"),
            return_date=search_options.get("return_date"),
        )