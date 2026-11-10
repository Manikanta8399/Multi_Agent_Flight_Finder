import math
import os
import re
from datetime import date

import requests

from src.flight_constants import NO_FLIGHTS_MESSAGE


DUFFEL_API_URL = "https://api.duffel.com/air/offer_requests"
DUFFEL_API_VERSION = "v2"
REQUEST_TIMEOUT_SECONDS = 30
SUPPLIER_TIMEOUT_MILLISECONDS = 10000
MAX_FLIGHT_RESULTS = 50
MIN_PASSENGERS = 1
MAX_PASSENGERS = 9
ALLOWED_CABIN_CLASSES = {"economy", "premium_economy", "business", "first"}
UNEXPECTED_RESPONSE_MESSAGE = "Duffel returned an unexpected response. Please try again later."

CITY_IATA_CODES = {
    "amsterdam": "AMS",
    "auckland": "AKL",
    "atlanta": "ATL",
    "barcelona": "BCN",
    "beijing": "BJS",
    "berlin": "BER",
    "buenos aires": "BUE",
    "boston": "BOS",
    "chicago": "CHI",
    "dallas": "DFW",
    "delhi": "DEL",
    "denver": "DEN",
    "dublin": "DUB",
    "dubai": "DXB",
    "honolulu": "HNL",
    "hong kong": "HKG",
    "istanbul": "IST",
    "las vegas": "LAS",
    "london": "LON",
    "los angeles": "LAX",
    "melbourne": "MEL",
    "mexico city": "MEX",
    "miami": "MIA",
    "montreal": "YMQ",
    "mumbai": "BOM",
    "new york": "NYC",
    "orlando": "ORL",
    "paris": "PAR",
    "prague": "PRG",
    "rome": "ROM",
    "san diego": "SAN",
    "san francisco": "SFO",
    "sao paulo": "SAO",
    "seoul": "SEL",
    "seattle": "SEA",
    "singapore": "SIN",
    "stockholm": "STO",
    "taipei": "TPE",
    "tel aviv": "TLV",
    "vancouver": "YVR",
    "sydney": "SYD",
    "tokyo": "TYO",
    "toronto": "YTO",
    "washington": "WAS",
    "zurich": "ZRH",
}


def _to_iata_code(location):
    cleaned_location = " ".join(str(location).strip().lower().split())
    if cleaned_location in CITY_IATA_CODES:
        return CITY_IATA_CODES[cleaned_location]

    if re.fullmatch(r"[a-z]{3}", cleaned_location):
        return cleaned_location.upper()

    return None


def _format_duration(duration):
    if not isinstance(duration, str):
        return None

    match = re.fullmatch(
        r"P(?:(?P<days>\d+)D)?T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?",
        duration,
    )
    if not match:
        return None

    days = int(match.group("days") or 0)
    hours = int(match.group("hours") or 0) + (days * 24)
    minutes = int(match.group("minutes") or 0)
    hours += minutes // 60
    minutes %= 60
    return f"{hours}h {minutes}m"


def _extract_valid_price(offer):
    try:
        price = float(offer["total_amount"])
    except (KeyError, TypeError, ValueError):
        return None

    if not math.isfinite(price) or price < 0:
        return None
    return price


def _extract_slice(slice_data):
    if not isinstance(slice_data, dict):
        return None

    segments = slice_data.get("segments")
    if not isinstance(segments, list) or not segments:
        return None

    duration = _format_duration(slice_data.get("duration"))
    if not duration:
        return None

    first_segment = segments[0]
    last_segment = segments[-1]
    if not isinstance(first_segment, dict) or not isinstance(last_segment, dict):
        return None

    departure_time = first_segment.get("departing_at")
    arrival_time = last_segment.get("arriving_at")
    if not departure_time or not arrival_time:
        return None

    return {
        "segments": segments,
        "first_segment": first_segment,
        "last_segment": last_segment,
        "duration": duration,
    }


def _extract_itinerary(offer):
    slices = offer.get("slices")
    if not isinstance(slices, list) or not slices or len(slices) > 2:
        return None

    itineraries = [_extract_slice(slice_data) for slice_data in slices]
    if any(itinerary is None for itinerary in itineraries):
        return None

    return itineraries


def _get_airline_name(offer, segments):
    operating_carriers = []
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        carrier = segment.get("operating_carrier") or segment.get("marketing_carrier") or {}
        if not isinstance(carrier, dict):
            continue
        carrier_name = carrier.get("name")
        if carrier_name and carrier_name not in operating_carriers:
            operating_carriers.append(carrier_name)

    if operating_carriers:
        return " / ".join(operating_carriers)

    owner = offer.get("owner")
    if isinstance(owner, dict):
        return owner.get("name", "Unknown airline")
    return "Unknown airline"


def _normalize_offer(offer, origin, destination, date, return_date=None):
    if not isinstance(offer, dict):
        return None

    price = _extract_valid_price(offer)
    itinerary = _extract_itinerary(offer)
    currency = offer.get("total_currency")
    if price is None or itinerary is None or not currency:
        return None

    outbound = itinerary[0]
    flight = {
        "airline": _get_airline_name(
            offer,
            [
                segment
                for slice_itinerary in itinerary
                for segment in slice_itinerary["segments"]
            ],
        ),
        "origin": origin,
        "destination": destination,
        "date": date,
        "departure_time": outbound["first_segment"]["departing_at"],
        "arrival_time": outbound["last_segment"]["arriving_at"],
        "duration": outbound["duration"],
        "stops": len(outbound["segments"]) - 1,
        "price": price,
        "currency": currency,
    }
    if len(itinerary) == 2:
        inbound = itinerary[1]
        flight.update({
            "return_date": return_date,
            "return_departure_time": inbound["first_segment"]["departing_at"],
            "return_arrival_time": inbound["last_segment"]["arriving_at"],
            "return_duration": inbound["duration"],
            "return_stops": len(inbound["segments"]) - 1,
        })
    return flight


def _failure_result(origin, destination, date, message, missing_fields=None):
    return {
        "success": False,
        "origin": origin,
        "destination": destination,
        "date": date,
        "missing_fields": missing_fields or [],
        "message": message,
        "results": [],
    }


def _validate_search_options(passenger_count, cabin_class, departure_date, return_date):
    if (
        not isinstance(passenger_count, int)
        or isinstance(passenger_count, bool)
        or not MIN_PASSENGERS <= passenger_count <= MAX_PASSENGERS
    ):
        return "Passenger count must be between 1 and 9 adults."

    if not isinstance(cabin_class, str) or cabin_class not in ALLOWED_CABIN_CLASSES:
        return "Choose a supported cabin class: economy, premium economy, business, or first."

    if (
        not isinstance(departure_date, str)
        or len(departure_date) != 10
        or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", departure_date)
    ):
        return "Travel date must use YYYY-MM-DD format."
    try:
        outbound_day = date.fromisoformat(departure_date)
    except ValueError:
        return "Travel date must use YYYY-MM-DD format."

    if return_date is not None:
        if (
            not isinstance(return_date, str)
            or len(return_date) != 10
            or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", return_date)
        ):
            return "Return date must use YYYY-MM-DD format."
        try:
            inbound_day = date.fromisoformat(return_date)
        except ValueError:
            return "Return date must use YYYY-MM-DD format."
        if inbound_day <= outbound_day:
            return "Return date must be after the departure date."

    return None


def _unmapped_location_fields(origin_code, destination_code):
    missing_fields = []
    if not origin_code:
        missing_fields.append("origin")
    if not destination_code:
        missing_fields.append("destination")
    return missing_fields


def search_duffel_flights(
    origin,
    destination,
    date,
    access_token=None,
    passenger_count=1,
    cabin_class="economy",
    return_date=None,
):
    token = access_token or os.getenv("DUFFEL_ACCESS_TOKEN", "").strip()
    if not token or token.startswith("replace_"):
        return _failure_result(
            origin,
            destination,
            date,
            "Duffel is selected, but DUFFEL_ACCESS_TOKEN is not configured in .env.",
        )

    origin_code = _to_iata_code(origin)
    destination_code = _to_iata_code(destination)
    missing_location_fields = _unmapped_location_fields(origin_code, destination_code)
    if missing_location_fields:
        return _failure_result(
            origin,
            destination,
            date,
            "I could not map a city to an IATA code. Use a supported city name or a 3-letter airport/city code.",
            missing_fields=missing_location_fields,
        )

    invalid_options_message = _validate_search_options(
        passenger_count, cabin_class, date, return_date
    )
    if invalid_options_message:
        return _failure_result(origin, destination, date, invalid_options_message)

    slices = [
        {
            "origin": origin_code,
            "destination": destination_code,
            "departure_date": date,
        }
    ]
    if return_date is not None:
        slices.append({
            "origin": destination_code,
            "destination": origin_code,
            "departure_date": return_date,
        })

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Duffel-Version": DUFFEL_API_VERSION,
    }
    payload = {
        "data": {
            "slices": slices,
            "passengers": [{"type": "adult"} for _ in range(passenger_count)],
            "cabin_class": cabin_class,
        }
    }
    params = {
        "return_offers": "true",
        "supplier_timeout": SUPPLIER_TIMEOUT_MILLISECONDS,
    }

    try:
        response = requests.post(
            DUFFEL_API_URL,
            headers=headers,
            params=params,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        response_data = response.json()
    except requests.RequestException:
        return _failure_result(
            origin,
            destination,
            date,
            "Duffel flight search failed. Check your connection and API token, then try again.",
        )

    if not isinstance(response_data, dict):
        return _failure_result(
            origin,
            destination,
            date,
            UNEXPECTED_RESPONSE_MESSAGE,
        )

    response_body = response_data.get("data")
    if not isinstance(response_body, dict):
        return _failure_result(
            origin,
            destination,
            date,
            UNEXPECTED_RESPONSE_MESSAGE,
        )

    offers = response_body.get("offers", [])
    if not isinstance(offers, list):
        return _failure_result(
            origin,
            destination,
            date,
            UNEXPECTED_RESPONSE_MESSAGE,
        )

    results = [
        normalized_offer
        for offer in offers[:MAX_FLIGHT_RESULTS]
        if (normalized_offer := _normalize_offer(offer, origin, destination, date, return_date))
    ]
    results.sort(key=lambda flight: flight["price"])

    if not results:
        return _failure_result(
            origin,
            destination,
            date,
            NO_FLIGHTS_MESSAGE,
        )

    return {
        "success": True,
        "origin": origin,
        "destination": destination,
        "date": date,
        "missing_fields": [],
        "results": results,
    }