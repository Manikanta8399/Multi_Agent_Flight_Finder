"""Bounded CrewAI tool for searching the configured flight provider."""

import json
from typing import Any, Dict, Optional, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from src.flight_search import search_flights


MAX_LOCATION_LENGTH = 100


class FlightSearchToolInput(BaseModel):
    """Validated input schema made available to the flight-search agent."""

    origin: str = Field(min_length=1, max_length=MAX_LOCATION_LENGTH)
    destination: str = Field(min_length=1, max_length=MAX_LOCATION_LENGTH)
    departure_date: str = Field(min_length=10, max_length=10)
    passenger_count: int = Field(default=1, ge=1, le=9)
    cabin_class: str = Field(default="economy", pattern="^(economy|premium_economy|business|first)$")
    return_date: Optional[str] = Field(default=None, min_length=10, max_length=10)


class FlightSearchTool(BaseTool):
    """Run one provider search using the already-understood user request."""

    name: str = "search_flights"
    description: str = (
        "Search the configured flight provider for the exact validated trip. "
        "Use this once for a complete flight request; never invent or alter its details."
    )
    args_schema: Type[BaseModel] = FlightSearchToolInput

    expected_origin: str = Field(exclude=True)
    expected_destination: str = Field(exclude=True)
    expected_departure_date: str = Field(exclude=True)
    passenger_count: int = Field(default=1, exclude=True)
    cabin_class: str = Field(default="economy", exclude=True)
    return_date: Optional[str] = Field(default=None, exclude=True)
    result: Optional[Dict[str, Any]] = Field(default=None, exclude=True)
    call_count: int = Field(default=0, exclude=True)
    on_search_complete: Any = Field(default=None, exclude=True)

    def _run(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        passenger_count: int = 1,
        cabin_class: str = "economy",
        return_date: Optional[str] = None,
    ) -> str:
        if self.call_count >= 1:
            return json.dumps({"success": False, "message": "Only one flight search is allowed per request."})

        self.call_count += 1
        requested_values = (
            origin,
            destination,
            departure_date,
            passenger_count,
            cabin_class,
            return_date,
        )
        validated_values = (
            self.expected_origin,
            self.expected_destination,
            self.expected_departure_date,
            self.passenger_count,
            self.cabin_class,
            self.return_date,
        )
        if requested_values != validated_values:
            self.result = {
                "success": False,
                "origin": self.expected_origin,
                "destination": self.expected_destination,
                "date": self.expected_departure_date,
                "missing_fields": [],
                "message": "The search tool rejected arguments that differ from the validated request.",
                "results": [],
            }
            return json.dumps(self.result)

        self.result = search_flights(
            self.expected_origin,
            self.expected_destination,
            self.expected_departure_date,
            passenger_count=self.passenger_count,
            cabin_class=self.cabin_class,
            return_date=self.return_date,
        )
        if callable(self.on_search_complete):
            self.on_search_complete()
        return json.dumps(self.result, ensure_ascii=False)
