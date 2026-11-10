import streamlit as st

from src.flight_parser import parse_flight_query
from src.flight_search import search_flights
from src.flight_summary import build_recommendation_cards, summarize_flights

st.set_page_config(page_title="AI Flight Finder", page_icon="✈️")
st.title("AI Flight Finder")
st.caption("A beginner-friendly flight assistant that parses flight requests and compares options.")

query = st.text_area(
    "Flight request",
    placeholder="Find flights from San Francisco to New York on September 21, 2027.",
)

if st.button("Search flights"):
    progress = st.empty()
    progress.info("Step 1 of 3: Checking your flight request...")
    parsed = parse_flight_query(query)
    message = parsed.get("message") or "I need a little more information."

    if not parsed["success"]:
        progress.empty()
        st.warning(message)
        st.write("Missing fields:", ", ".join(parsed.get("missing_fields", [])))
        st.write("Example: 'Find flights from San Francisco to New York on September 21, 2027.'")
    else:
        progress.info("Step 2 of 3: Searching for matching flights...")
        st.success("I understood the request.")
        st.write({
            "origin": parsed["origin"],
            "destination": parsed["destination"],
            "date": parsed["date"],
        })

        flights = search_flights(parsed["origin"], parsed["destination"], parsed["date"])

        if flights["success"]:
            progress.info("Step 3 of 3: Comparing flights and preparing your summary...")
            with st.spinner("Almost there — asking the AI assistant to compare your options..."):
                summary = summarize_flights(flights["results"])
            recommendation_cards = build_recommendation_cards(summary)
            progress.empty()

            st.subheader("Summary")
            st.info(summary["summary"])

            if recommendation_cards:
                st.subheader("Flight recommendations")
                recommendations = (
                    ("Cheapest", recommendation_cards["cheapest"]),
                    ("Fastest", recommendation_cards["fastest"]),
                    ("Best overall", recommendation_cards["best_choice"]),
                )

                for label, details in recommendations:
                    with st.container(border=True):
                        st.markdown(f"**{label}**")
                        st.write(details)

            st.subheader("Top flight options")
            st.dataframe(
                [
                    {
                        "Airline": flight["airline"],
                        "Departure": flight["departure_time"],
                        "Arrival": flight["arrival_time"],
                        "Duration": flight["duration"],
                        "Stops": flight["stops"],
                        "Price": f"${flight['price']}",
                    }
                    for flight in flights["results"]
                ],
                width="stretch",
            )
        else:
            progress.empty()
            if flights.get("missing_fields"):
                st.warning("Please provide all required flight details.")
                st.write("Missing fields:", ", ".join(flights["missing_fields"]))
            else:
                st.info(flights.get("message", "No flights found for this route and date."))
