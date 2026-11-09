"""Clinic-aware chatbot flow. Keeps translations.py, intent_classifier.py and memory.py."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from intent_classifier import classify_intent
from memory import add_message
from translations import TRANSLATIONS

from google_calendar import (
    get_available_slots,
    book_appointment
)


def tr(language):
    return TRANSLATIONS.get(
        language,
        TRANSLATIONS.get("de", {})
    )


def clinic_treatments(clinic, language):

    result = []

    for key, treatment in clinic.get("treatments", {}).items():

        names = treatment.get("names", {})

        name = (
            names.get(language)
            or names.get("de")
            or key
        )

        result.append((name, treatment))

    return result


def no_clinic_data(language):

    return {
        "de": "Für diese Praxis sind noch keine Behandlungen hinterlegt.",
        "en": "No treatments have been configured for this clinic yet.",
        "hun": "Ehhez a klinikához még nincsenek kezelések beállítva."
    }.get(
        language,
        "No treatments have been configured for this clinic yet."
    )


def _text(T, key, fallback):
    return T.get(key, fallback)


def _date_suggestions(clinic):

    tz = ZoneInfo(
        clinic.get("timezone", "Europe/Budapest")
    )

    today = datetime.now(tz).date()

    return [
        (today + timedelta(days=n)).isoformat()
        for n in (1, 2, 7)
    ]


def _price_reply(clinic_data, language):

    lines = [
        f"🦷 {name} — {data.get('price')}"
        for name, data in clinic_data
        if data.get("price")
    ]

    heading = {
        "de": "Unsere Preise:",
        "en": "Our prices:",
        "hun": "Áraink:"
    }.get(language, "Our prices:")

    return heading + (
        "\n\n" + "\n".join(lines)
        if lines else ""
    )


def handle_message(
    user_id,
    message,
    session,
    language,
    clinic,
    clinic_id
):

    T = tr(language)

    clinic_data = clinic_treatments(
        clinic,
        language
    )

    treatment_names = [
        name for name, _ in clinic_data
    ]

    raw = (message or "").strip()
    text = raw.lower()

    # =================================
    # FAQ INTERRUPTS - WORK DURING BOOKING
    # =================================

    # Treatments
    if any(word in text for word in (
        "treatment",
        "treatments",
        "behandlung",
        "behandlungen",
        "kezelés",
        "kezelések"
    )):
        if not clinic_data:
            return {"reply": no_clinic_data(language)}

        return {
            "reply": _text(
                T,
                "treatments_reply",
                "We offer the following treatments:"
            ),
            "suggestions": treatment_names
        }

    # Prices
    if any(word in text for word in (
        "price",
        "prices",
        "cost",
        "preis",
        "preise",
        "ár",
        "árak"
    )):
        if not clinic_data:
            return {"reply": no_clinic_data(language)}

        return {
            "reply": _price_reply(clinic_data, language),
            "suggestions": treatment_names
        }

    # Insurance
    if (
        "insurance" in text
        or "versicherung" in text
        or "biztosítás" in text
    ):
        return {
            "reply": _text(
                T,
                "insurance_reply",
                "Please contact the clinic for insurance information."
            ),
            "suggestions": T.get("insurance_suggestions", [])
        }


    # =================================
    # APPOINTMENT STAGES
    # =================================

    stage = session.get("stage")

    if stage == "awaiting_treatment":

        match = next(
            (
                (name, data)
                for name, data in clinic_data
                if name.lower() == text
            ),
            None
        )

        if not match:

            return {
                "reply": _text(
                    T,
                    "booking_question",
                    "Which treatment would you like to book?"
                ),
                "suggestions": treatment_names
            }

        name, data = match

        session.update({
            "treatment": name,
            "treat": name,
            "duration_minutes": int(
                data.get("duration") or 30
            ),
            "stage": "awaiting_date"
        })

        return {
            "reply": _text(
                T,
                "which_date",
                "Please choose a date (YYYY-MM-DD)."
            ),
            "suggestions": _date_suggestions(clinic)
        }

    # =================================
    # DATE SELECTION
    # =================================

    if stage == "awaiting_date":

        try:

            selected = datetime.strptime(
                raw,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            return {
                "reply": (
                    "Please enter the date in YYYY-MM-DD format, "
                    "e.g. 2026-11-10."
                )
            }

        tz = ZoneInfo(
            clinic.get("timezone", "Europe/Budapest")
        )

        if selected < datetime.now(tz).date():

            return {
                "reply": "Please choose a future date."
            }

        duration = int(
            session.get("duration_minutes", 30)
        )

        try:

            slots = get_available_slots(
                selected.isoformat(),
                clinic_id,
                duration
            )

        except Exception as exc:

            print(
                "Calendar availability error:",
                clinic_id,
                repr(exc)
            )

            return {
                "reply": (
                    "Sorry, I could not check this clinic's calendar. "
                    "Please try again later or contact the clinic."
                )
            }

        if not slots:

            return {
                "reply": (
                    "Sorry, there are no available appointments "
                    "on this date. Please choose another date."
                ),
                "suggestions": _date_suggestions(clinic)
            }

        slot_map = {
            datetime.fromisoformat(
                slot["start"]
            ).strftime("%H:%M"): slot["start"]
            for slot in slots
        }

        session.update({
            "date": selected.isoformat(),
            "slot_map": slot_map,
            "stage": "awaiting_time"
        })

        return {
            "reply": (
                f"Available appointments on {selected.isoformat()}:"
            ),
            "suggestions": list(slot_map)
        }

    # =================================
    # TIME SELECTION
    # =================================

    if stage == "awaiting_time":

        slot_map = session.get("slot_map", {})

        if raw not in slot_map:

            return {
                "reply": (
                    "This time is not available. "
                    "Please select one of the available times."
                ),
                "suggestions": list(slot_map)
            }

        session.update({
            "time": raw,
            "start_time": slot_map[raw],
            "stage": "awaiting_name"
        })

        return {
            "reply": _text(
                T,
                "your_name",
                "Please enter your full name."
            )
        }

    # =================================
    # NAME
    # =================================

    if stage == "awaiting_name":

        if len(raw) < 2:

            return {
                "reply": "Please enter your full name."
            }

        session.update({
            "name": raw,
            "stage": "awaiting_phone"
        })

        return {
            "reply": _text(
                T,
                "phone",
                "Please enter your phone number."
            )
        }

    # =================================
    # PHONE + GOOGLE CALENDAR BOOKING
    # =================================

    if stage == "awaiting_phone":

        if len(raw) < 5:

            return {
                "reply": "Please enter a valid phone number."
            }

        session["phone"] = raw

        try:

            result = book_appointment(
                start_time=session["start_time"],
                patient_name=session["name"],
                patient_phone=session["phone"],
                treatment=session.get(
                    "treatment",
                    "Consultation"
                ),
                clinic_id=clinic_id,
                duration_minutes=int(
                    session.get("duration_minutes", 30)
                )
            )

        except Exception as exc:

            print(
                "Calendar booking error:",
                clinic_id,
                repr(exc)
            )

            session["stage"] = "awaiting_date"

            return {
                "reply": (
                    "Sorry, the appointment could not be booked. "
                    "Please choose another date."
                ),
                "suggestions": _date_suggestions(clinic)
            }

        session["stage"] = None

        confirmation = _text(
            T,
            "confirmation",
            "Appointment confirmed for {name}: {treatment}, {date} at {time}."
        ).format(
            name=session["name"],
            treatment=session.get(
                "treatment",
                "Consultation"
            ),
            date=session["date"],
            time=session["time"]
        )

        add_message(
            user_id,
            "assistant",
            confirmation
        )

        return {
            "reply": confirmation,
            "booking_confirmed": True,
            "event_link": result.get("event_link")
        }

    # =================================
    # NORMAL INTENT HANDLING
    # =================================

    if not text:

        return {
            "reply": _text(
                T,
                "how_can_i_help",
                "How can I help you?"
            ),
            "suggestions": T.get(
                "main_suggestions",
                []
            )
        }

    # Treatments

    if any(
        word in text
        for word in (
            "treatment",
            "treatments",
            "behandlungen",
            "behandlung",
            "kezelés",
            "kezelések"
        )
    ):

        if not clinic_data:
            return {
                "reply": no_clinic_data(language)
            }

        return {
            "reply": _text(
                T,
                "treatments_reply",
                "We offer the following treatments:"
            ),
            "suggestions": treatment_names
        }

    # Prices

    if any(
        word in text
        for word in (
            "price",
            "prices",
            "cost",
            "preis",
            "preise",
            "ár",
            "árak"
        )
    ):

        if not clinic_data:
            return {
                "reply": no_clinic_data(language)
            }

        return {
            "reply": _price_reply(
                clinic_data,
                language
            ),
            "suggestions": treatment_names
        }

    # Insurance

    if (
        "insurance" in text
        or "versicherung" in text
        or "biztosítás" in text
    ):

        return {
            "reply": _text(
                T,
                "insurance_reply",
                "Please contact the clinic for insurance information."
            ),
            "suggestions": T.get(
                "insurance_suggestions",
                []
            )
        }

    # Intent classifier

    try:

        classified = classify_intent(
            user_id,
            text,
            language
        )

    except Exception as exc:

        print(
            "Intent classifier error:",
            repr(exc)
        )

        return {
            "reply": _text(
                T,
                "error_reply",
                "Sorry, something went wrong. Please try again."
            )
        }

    intent = classified.get(
        "intent",
        "unknown"
    )

    if classified.get("confidence", 0) < 0.1:
        intent = "unknown"

    if intent == "booking":

        if not treatment_names:
            return {
                "reply": no_clinic_data(language)
            }

        session["stage"] = "awaiting_treatment"

        return {
            "reply": _text(
                T,
                "booking_question",
                "Which treatment would you like to book?"
            ),
            "suggestions": treatment_names
        }

    if intent == "pricing_objection":

        return {
            "reply": (
                _price_reply(clinic_data, language)
                if clinic_data
                else no_clinic_data(language)
            ),
            "suggestions": treatment_names
        }

    if intent == "treatments":

        return {
            "reply": (
                _text(
                    T,
                    "treatments_reply",
                    "We offer the following treatments:"
                )
                if treatment_names
                else no_clinic_data(language)
            ),
            "suggestions": treatment_names
        }

    key_by_intent = {
        "emergency": "emergency_reply",
        "insurance": "insurance_reply",
        "Location_Hours": "location_reply",
        "Human": "human_reply",
        "welcome_message": "welcome",
        "unknown": "unknown_reply"
    }

    key = key_by_intent.get(
        intent,
        "unknown_reply"
    )

    reply = _text(
        T,
        key,
        "Sorry, I did not understand. Could you rephrase that?"
    )

    add_message(
        user_id,
        "assistant",
        reply
    )

    response = {
        "reply": reply
    }

    suggestions_key = {
        "insurance": "insurance_suggestions"
    }.get(intent)

    if suggestions_key and T.get(suggestions_key):

        response["suggestions"] = T[suggestions_key]

    return response