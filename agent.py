
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from intent_classifier import classify_intent
from memory import add_message
from translations import TRANSLATIONS
from google_calendar import get_available_slots, book_appointment


TIMEZONE = ZoneInfo("Europe/Budapest")


def tr(language):
    return TRANSLATIONS.get(language, TRANSLATIONS["de"])


def get_date_suggestions():
    today = datetime.now(TIMEZONE).date()

    return [
        (today + timedelta(days=1)).isoformat(),
        (today + timedelta(days=2)).isoformat(),
        (today + timedelta(days=7)).isoformat()
    ]


def handle_message(user_id, message, session, language):
    T = tr(language)

    raw_message = message.strip()
    message = raw_message.lower()

    # =================================
    # TREATMENT SELECTION
    # =================================

    translated_treatments = {
        treatment.lower(): treatment
        for treatment in T["treatments"]
    }

    if message in translated_treatments:
        selected_treatment = translated_treatments[message]

        session["selected_treatment"] = selected_treatment
        session["behandlung"] = selected_treatment
        session["treat"] = selected_treatment
        session["treatment"] = selected_treatment
        session["stage"] = "awaiting_date"

        return {
            "reply": T["which_date"],
            "suggestions": get_date_suggestions()
        }

    # =================================
    # APPOINTMENT FLOW
    # =================================

    if session.get("stage") == "awaiting_treatment":

        session["behandlung"] = raw_message
        session["treatment"] = raw_message
        session["treat"] = raw_message

        session["stage"] = "awaiting_date"

        return {
            "reply": T["which_date"],
            "suggestions": get_date_suggestions()
        }

    elif session.get("stage") == "awaiting_date":

        # Expect YYYY-MM-DD
        try:
            selected_date = datetime.strptime(
                raw_message, "%Y-%m-%d"
            ).date()

        except ValueError:
            return {
                "reply": (
                    "Please enter the date in YYYY-MM-DD format. "
                    "Example: 2026-11-10"
                )
            }

        if selected_date < datetime.now(TIMEZONE).date():
            return {
                "reply": "Please choose a future date."
            }

        session["date"] = selected_date.isoformat()

        try:
            available_slots = get_available_slots(
                session["date"]
            )

        except Exception as e:
            print("Google Calendar availability error:", e)

            return {
                "reply": (
                    "Sorry, I could not check the calendar. "
                    "Please try again later."
                )
            }

        if not available_slots:
            return {
                "reply": (
                    "Sorry, there are no available appointments "
                    "on this date. Please choose another date."
                ),
                "suggestions": get_date_suggestions()
            }

        # Map displayed times to full ISO datetime values
        slot_map = {}

        for slot in available_slots:
            start_datetime = datetime.fromisoformat(
                slot["start"]
            )

            display_time = start_datetime.strftime("%H:%M")

            slot_map[display_time] = slot["start"]

        session["slot_map"] = slot_map
        session["stage"] = "awaiting_time"

        return {
            "reply": f"Available appointments on {session['date']}:",
            "suggestions": list(slot_map.keys())
        }

    elif session.get("stage") == "awaiting_time":

        selected_time = raw_message.strip()

        slot_map = session.get("slot_map", {})

        if selected_time not in slot_map:
            return {
                "reply": (
                    "This time is not available. "
                    "Please select one of the available times."
                ),
                "suggestions": list(slot_map.keys())
            }

        session["time"] = selected_time
        session["start_time"] = slot_map[selected_time]

        session["stage"] = "awaiting_name"

        return {
            "reply": T["your_name"]
        }

    elif session.get("stage") == "awaiting_name":

        if len(raw_message) < 2:
            return {
                "reply": "Please enter your full name."
            }

        session["name"] = raw_message
        session["stage"] = "awaiting_phone"

        return {
            "reply": T["phone"]
        }

    elif session.get("stage") == "awaiting_phone":

        if len(raw_message) < 5:
            return {
                "reply": "Please enter a valid phone number."
            }

        session["phone"] = raw_message

        # Create a real Google Calendar event
        try:
            result = book_appointment(
                start_time=session["start_time"],
                patient_name=session["name"],
                patient_phone=session["phone"],
                treatment=session.get(
                    "treatment",
                    "Consultation"
                )
            )

            print("GOOGLE CALENDAR BOOKING:", result)

        except Exception as e:
            print("Google Calendar booking error:", e)

            session["stage"] = "awaiting_date"

            return {
                "reply": (
                    "Sorry, this appointment could not be booked. "
                    "Please choose another date."
                ),
                "suggestions": get_date_suggestions()
            }

        session["stage"] = None

        confirmation = T["confirmation"].format(
            name=session["name"],
            treatment=session.get(
                "treatment",
                "Consultation"
            ),
            date=session["date"],
            time=session["time"]
        )

        add_message(user_id, "assistant", confirmation)

        return {
            "reply": confirmation,
            "booking_confirmed": True,
            "event_link": result.get("event_link")
        }

    # =================================
    # NORMAL INTENT HANDLING
    # =================================

    if not message:
        return {
            "reply": T["how_can_i_help"],
            "suggestions": T["main_suggestions"]
        }

    if (
        "treatment" in message
        or "treatments" in message
        or "behandlungen" in message
        or "kezelés" in message
        or "kezelések" in message
    ):
        return {
            "reply": T["treatments_reply"],
            "suggestions": list(T["treatments"])
        }

    if "price" in message or "cost" in message:
        return {
            "reply": T["pricing_reply"],
            "suggestions": T["pricing_suggestions"]
        }

    if "insurance" in message:
        return {
            "reply": T["insurance_reply"],
            "suggestions": T["insurance_suggestions"]
        }

    result = classify_intent(user_id, message, language)

    intent = result["intent"]
    confidence = result["confidence"]

    print("DEBUG INTENT:", result)

    if confidence < 0.1:
        intent = "unknown"

    if intent == "booking":

        session["stage"] = "awaiting_treatment"

        return {
            "reply": T["booking_question"],
            "suggestions": T["booking_treatments"]
        }

    elif intent == "pricing_objection":
        reply = T["pricing_reply"]
        suggestions = T["pricing_suggestions"]

    elif intent == "treatments":
        reply = T["treatments_reply"]
        suggestions = T["treatments"]

    elif intent == "emergency":
        reply = T["emergency_reply"]
        suggestions = None

    elif intent == "insurance":
        reply = T["insurance_reply"]
        suggestions = T["insurance_suggestions"]

    elif intent == "Location_Hours":
        reply = T["location_reply"]
        suggestions = None

    elif intent == "Human":
        reply = T["human_reply"]
        suggestions = None

    elif intent == "welcome_message":
        reply = T["welcome"]
        suggestions = None

    else:
        reply = T["unknown_reply"]
        suggestions = None

    add_message(user_id, "assistant", reply)

    response = {"reply": reply}

    if suggestions is not None:
        response["suggestions"] = suggestions

    return response
