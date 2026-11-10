SAMPLE_ORIGIN = "San Francisco"
SAMPLE_DESTINATION = "New York"


def search_flights(origin, destination, date):
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
            "message": "No flights found for this route and date.",
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
