"""Compatibility entry point for the flight-finder master agent."""

from src.agents.master_agent import FlightFinderMasterAgent

def run_flight_finder(query, on_progress=None):
    """Run the master agent while preserving the original function interface."""
    return FlightFinderMasterAgent().run(query, on_progress=on_progress)