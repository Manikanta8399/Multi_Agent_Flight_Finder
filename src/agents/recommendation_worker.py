"""Worker responsible for comparing flight options and writing a summary."""

from src.flight_summary import summarize_flights


class FlightRecommendationWorkerAgent:
    def run(self, flights):
        return summarize_flights(flights)