import streamlit as st
from dotenv import load_dotenv

from src.agents.master_agent import FlightFinderMasterAgent
from src.agents.request_worker import (
    build_clarified_query,
    build_search_correction_request,
)
from src.flight_summary import build_recommendation_cards

load_dotenv()

st.set_page_config(page_title="AI Flight Finder", page_icon="✈️")
st.title("AI Flight Finder")
st.caption(
    "CrewAI coordinates a local Ollama-powered Flight Search Agent and "
    "Flight Recommendation Agent."
)

query = st.text_area(
    "Flight request",
    placeholder="Find flights from San Francisco to New York on September 21, 2027.",
    max_chars=500,
    key="flight_request_text",
)
option_col1, option_col2 = st.columns(2)
with option_col1:
    passenger_count = st.selectbox("Adult travelers", range(1, 10), index=0)
with option_col2:
    cabin_class = st.selectbox(
        "Cabin class",
        ("economy", "premium_economy", "business", "first"),
        format_func=lambda value: value.replace("_", " ").title(),
    )
round_trip = st.checkbox("Round trip")
return_date = ""
if round_trip:
    return_date = st.text_input(
        "Return date",
        placeholder="YYYY-MM-DD, for example 2027-09-28",
        max_chars=10,
    )

search_options = {
    "passenger_count": passenger_count,
    "cabin_class": cabin_class,
    "return_date": return_date if round_trip else None,
}

PENDING_REQUEST_KEY = "pending_flight_request"
SEARCH_RESULT_KEY = "flight_search_result"
VALIDATION_MESSAGE_KEY = "flight_validation_message"
st.session_state.setdefault(PENDING_REQUEST_KEY, None)
st.session_state.setdefault(SEARCH_RESULT_KEY, None)
st.session_state.setdefault(VALIDATION_MESSAGE_KEY, None)

missing_field_prompts = {
    "origin": ("Where are you flying from?", "Enter a city name or 3-letter code."),
    "destination": ("Where would you like to go?", "Enter a city name or 3-letter code."),
    "date": ("What date do you want to travel?", "Example: September 21, 2027."),
}


def run_search(request_text, options):
    progress = st.empty()
    progress_messages = {
        "validating": "Step 1 of 3: Checking your flight request...",
        "searching": "Step 2 of 3: Flight Search Agent is invoking the permitted search tool...",
        "summarizing": "Step 3 of 3: Flight Recommendation Agent is comparing the returned offers...",
    }

    def show_progress(stage):
        progress.info(progress_messages[stage])

    master_agent = FlightFinderMasterAgent()
    result = master_agent.run(
        request_text,
        on_progress=show_progress,
        search_options=options,
    )
    progress.empty()
    return result


def save_search_result(result):
    if result["stage"] == "validation":
        parsed = result["parsed"]
        if parsed.get("missing_fields"):
            st.session_state[PENDING_REQUEST_KEY] = parsed
            st.session_state[VALIDATION_MESSAGE_KEY] = None
        else:
            st.session_state[PENDING_REQUEST_KEY] = None
            st.session_state[VALIDATION_MESSAGE_KEY] = (
                parsed.get("message") or "I couldn't understand that request. Please rephrase it."
            )
    elif result["stage"] == "search":
        correction_request = build_search_correction_request(
            result["parsed"], result["flights"]
        )
        if correction_request:
            st.session_state[PENDING_REQUEST_KEY] = correction_request
            st.session_state[VALIDATION_MESSAGE_KEY] = None
            st.session_state[SEARCH_RESULT_KEY] = None
            return

        st.session_state[PENDING_REQUEST_KEY] = None
        st.session_state[VALIDATION_MESSAGE_KEY] = None
        st.session_state[SEARCH_RESULT_KEY] = result
    else:
        st.session_state[PENDING_REQUEST_KEY] = None
        st.session_state[VALIDATION_MESSAGE_KEY] = None
        st.session_state[SEARCH_RESULT_KEY] = result


def render_search_result(result):
    parsed = result["parsed"]
    st.success("I understood the request.")
    st.write({
        "origin": parsed["origin"],
        "destination": parsed["destination"],
        "date": parsed["date"],
    })

    flights = result["flights"]

    if result["success"]:
        summary = result["summary"]
        recommendation_cards = build_recommendation_cards(summary)

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
                    "Return departure": flight.get("return_departure_time", "—"),
                    "Return arrival": flight.get("return_arrival_time", "—"),
                    "Duration": flight["duration"],
                    "Stops": flight["stops"],
                    "Price": f"{flight.get('currency', 'USD')} {flight['price']:,.2f}",
                }
                for flight in flights["results"]
            ],
            width="stretch",
        )
    elif flights.get("missing_fields"):
        st.warning("Please provide all required flight details.")
        st.write("Missing fields:", ", ".join(flights["missing_fields"]))
    else:
        st.info(flights.get("message", "No flights found for this route and date."))


if st.button("Search flights"):
    st.session_state[SEARCH_RESULT_KEY] = None
    st.session_state[VALIDATION_MESSAGE_KEY] = None
    save_search_result(run_search(query, search_options))

if st.session_state[VALIDATION_MESSAGE_KEY]:
    st.warning(st.session_state[VALIDATION_MESSAGE_KEY])
    st.write("Example: 'Find flights from San Francisco to New York on September 21, 2027.'")

pending_request = st.session_state[PENDING_REQUEST_KEY]
if pending_request:
    st.info(pending_request.get("message") or "I need a little more information.")
    with st.form("flight_clarification_form"):
        answers = {}
        for field in pending_request["missing_fields"]:
            label, placeholder = missing_field_prompts[field]
            answers[field] = st.text_input(label, placeholder=placeholder, key=f"clarify_{field}")

        submitted = st.form_submit_button("Continue search")

    if submitted:
        clarified_query = build_clarified_query(pending_request, answers)
        if clarified_query:
            st.session_state[SEARCH_RESULT_KEY] = None
            save_search_result(run_search(clarified_query, search_options))
        else:
            st.warning("Please fill in each requested detail before continuing.")

if st.session_state[SEARCH_RESULT_KEY]:
    render_search_result(st.session_state[SEARCH_RESULT_KEY])
