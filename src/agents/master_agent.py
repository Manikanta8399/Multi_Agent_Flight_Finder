"""Master agent that coordinates the specialized flight-finder workers."""

from src.agents.recommendation_worker import FlightRecommendationWorkerAgent
from src.agents.request_worker import RequestUnderstandingWorkerAgent
from src.agents.search_worker import FlightSearchWorkerAgent


class FlightFinderMasterAgent:
    def __init__(
        self,
        request_worker=None,
        search_worker=None,
        recommendation_worker=None,
        crew_runner=None,
    ):
        self.request_worker = request_worker or RequestUnderstandingWorkerAgent()
        self.search_worker = search_worker or FlightSearchWorkerAgent()
        self.recommendation_worker = (
            recommendation_worker or FlightRecommendationWorkerAgent()
        )
        self.crew_runner = crew_runner
        if (
            self.crew_runner is None
            and search_worker is None
            and recommendation_worker is None
        ):
            from src.agents.crewai_flight_crew import CrewAIFlightCrew

            self.crew_runner = CrewAIFlightCrew()

    def run(self, query, on_progress=None, search_options=None):
        if on_progress:
            on_progress("validating")
        parsed_request = self.request_worker.run(query)
        if not parsed_request["success"]:
            return {
                "success": False,
                "stage": "validation",
                "parsed": parsed_request,
                "flights": None,
                "summary": None,
            }

        if on_progress:
            on_progress("searching")
        if self.crew_runner:
            crew_result = self.crew_runner.run(
                parsed_request,
                search_options=search_options,
                on_progress=on_progress,
            )
            flights = crew_result["flights"]
            if not flights["success"]:
                return {
                    "success": False,
                    "stage": "search",
                    "parsed": parsed_request,
                    "flights": flights,
                    "summary": None,
                }

            return {
                "success": True,
                "stage": "complete",
                "parsed": parsed_request,
                "flights": flights,
                "summary": crew_result["summary"],
            }

        flights = self.search_worker.run(parsed_request, search_options=search_options)
        if not flights["success"]:
            return {
                "success": False,
                "stage": "search",
                "parsed": parsed_request,
                "flights": flights,
                "summary": None,
            }

        if on_progress:
            on_progress("summarizing")
        summary = self.recommendation_worker.run(flights["results"])
        return {
            "success": True,
            "stage": "complete",
            "parsed": parsed_request,
            "flights": flights,
            "summary": summary,
        }