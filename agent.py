"""Clinic-aware chatbot flow.

Keeps:
- translations.py
- intent_classifier.py
- memory.py
- google_calendar.py
"""

import re
import traceback
import unicodedata

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from intent_classifier import classify_intent
from memory import add_message
from translations import TRANSLATIONS

from google_calendar import (
    get_available_slots,
    book_appointment,
)


# ============================================================
# TRANSLATIONS
# ============================================================

def tr(language):
    return TRANSLATIONS.get(
        language,
        TRANSLATIONS.get("de", {})
    )


def _text(T, key, fallback):
    return T.get(key, fallback)


def _localized(language, de, en, hu):
    return {
        "de": de,
        "en": en,
        "hun": hu,
        "hu": hu,
    }.get(language, en)


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def _normalize(value):
    """Normalize text for reliable matching."""

    value = str(value or "").strip().lower()

    value = unicodedata.normalize(
        "NFKD",
        value
    )

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )

    return re.sub(
        r"\s+",
        " ",
        value
    )


def _contains_phrase(text, phrases):
    normalized = _normalize(text)

    for phrase in phrases:
        phrase = _normalize(phrase)

        if not phrase:
            continue

        pattern = (
            r"(?<!\w)"
            + re.escape(phrase)
            + r"(?!\w)"
        )

        if re.search(pattern, normalized):
            return True

    return False


# ============================================================
# CLINIC DATA
# ============================================================

def clinic_treatments(clinic, language):

    result = []

    for key, treatment in clinic.get(
        "treatments",
        {}
    ).items():

        names = treatment.get(
            "names",
            {}
        )

        name = (
            names.get(language)
            or names.get("de")
            or names.get("en")
            or key
        )

        result.append(
            (name, treatment)
        )

    return result


def no_clinic_data(language):

    return _localized(
        language,
        "Für diese Praxis sind noch keine Behandlungen hinterlegt.",
        "No treatments have been configured for this clinic yet.",
        "Ehhez a klinikához még nincsenek kezelések beállítva."
    )


# ============================================================
# DATE SUGGESTIONS
# ============================================================

def _date_suggestions(clinic):

    tz = ZoneInfo(
        clinic.get(
            "timezone",
            "Europe/Budapest"
        )
    )

    today = datetime.now(tz).date()

    return [
        (today + timedelta(days=n)).isoformat()
        for n in (1, 2, 7)
    ]


# ============================================================
# PRICE REPLY
# ============================================================

def _price_reply(clinic_data, language):

    lines = [
        f"🦷 {name} — {data.get('price')}"
        for name, data in clinic_data
        if data.get("price")
    ]

    heading = _localized(
        language,
        "Unsere Preise:",
        "Our prices:",
        "Áraink:"
    )

    return heading + (
        "\n\n" + "\n".join(lines)
        if lines
        else "\n\nPlease contact the clinic for pricing information."
    )


# ============================================================
# INTENT DETECTION
# ============================================================

def _is_booking_request(text):

    booking_phrases = (

        # English
        "appointment",
        "book an appointment",
        "make an appointment",
        "i need an appointment",
        "i want an appointment",
        "i would like an appointment",
        "i need treatment",
        "i need a treatment",
        "book a treatment",

        # German
        "termin",
        "termin buchen",
        "einen termin",
        "ich brauche einen termin",
        "ich möchte einen termin",
        "ich benoetige einen termin",
        "behandlung buchen",
        "ich brauche eine behandlung",

        # Hungarian
        "időpont",
        "idopont",
        "időpontot szeretnék",
        "idopontot szeretnek",
        "időpontot kérek",
        "idopontot kerek",
        "időpontot foglalnék",
        "idopontot foglalnek",
        "foglalni szeretnék",
        "foglalni szeretnek",
        "szeretnék foglalni",
        "szeretnek foglalni",
        "kezelésre",
        "kezelesre",
        "kezelést szeretnék",
        "kezelest szeretnek",
        "szükségem lenne kezelésre",
        "szuksegem lenne kezelesre",
    )

    return _contains_phrase(
        text,
        booking_phrases
    )


def _is_treatments_question(text):

    return _contains_phrase(
        text,
        (
            "treatment",
            "treatments",
            "what treatments",
            "behandlung",
            "behandlungen",
            "welche behandlungen",
            "kezelés",
            "kezelések",
            "milyen kezelések",
            "milyen kezelesek",
            "kezelési lista",
            "kezelesi lista",
        )
    )


def _is_prices_question(text):

    return _contains_phrase(
        text,
        (
            "price",
            "prices",
            "cost",
            "how much",
            "pricing",
            "preis",
            "preise",
            "kosten",
            "was kostet",
            "ár",
            "árak",
            "mennyibe kerül",
            "mennyibe kerul",
        )
    )


def _is_insurance_question(text):

    return _contains_phrase(
        text,
        (
            "insurance",
            "versicherung",
            "biztosítás",
            "biztositas",
        )
    )


# ============================================================
# MAIN CHAT HANDLER
# ============================================================

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
        name
        for name, _ in clinic_data
    ]

    raw = (message or "").strip()
    text = raw.lower()
    stage = session.get("stage")

    # ========================================================
    # DIRECT TREATMENT SELECTION
    # A clicked treatment button starts the booking process.
    # ========================================================

    if stage is None:

        normalized_input = _normalize(raw)

        selected_treatment = next(
            (
                (name, data)
                for name, data in clinic_data
                if _normalize(name) == normalized_input
            ),
            None
        )

        if selected_treatment:

            name, data = selected_treatment

            try:
                duration = int(data.get("duration") or 30)
            except (TypeError, ValueError):
                duration = 30

            if duration <= 0:
                duration = 30

            session.update({
                "treatment": name,
                "treat": name,
                "duration_minutes": duration,
                "stage": "awaiting_date"
            })

            return {
                "reply": _text(
                    T,
                    "which_date",
                    _localized(
                        language,
                        "Bitte wählen Sie ein Datum.",
                        "Please choose a date.",
                        "Kérem, válasszon egy dátumot."
                    )
                ),
                "suggestions": _date_suggestions(clinic)
            }

    stage = session.get("stage")

    # ========================================================
    # EMPTY MESSAGE
    # ========================================================

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

    # ========================================================
    # BOOKING REQUEST PRIORITY
    #
    # IMPORTANT:
    # "Kezelésre lenne szükségem" must start booking.
    # It must NOT trigger the treatment FAQ.
    # ========================================================

    if stage is None and _is_booking_request(text):

        if not treatment_names:

            return {
                "reply": no_clinic_data(language)
            }

        session.clear()

        session["stage"] = "awaiting_treatment"

        return {
            "reply": _text(
                T,
                "booking_question",
                _localized(
                    language,
                    "Welche Behandlung möchten Sie buchen?",
                    "Which treatment would you like to book?",
                    "Milyen kezelésre szeretne időpontot foglalni?"
                )
            ),
            "suggestions": treatment_names
        }

    # ========================================================
    # FAQ INTERRUPTS
    #
    # These questions can be answered during booking.
    # The current booking stage is preserved.
    # ========================================================

    # Treatments FAQ
    if _is_treatments_question(text):

        if not clinic_data:

            return {
                "reply": no_clinic_data(language)
            }

        return {
            "reply": _text(
                T,
                "treatments_reply",
                _localized(
                    language,
                    "Wir bieten folgende Behandlungen an:",
                    "We offer the following treatments:",
                    "Az alábbi kezeléseket kínáljuk:"
                )
            ),
            "suggestions": treatment_names
        }

    # Prices FAQ
    if _is_prices_question(text):

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

    # Insurance FAQ
    if _is_insurance_question(text):

        return {
            "reply": _text(
                T,
                "insurance_reply",
                _localized(
                    language,
                    "Bitte kontaktieren Sie die Praxis bezüglich Versicherungsinformationen.",
                    "Please contact the clinic for insurance information.",
                    "A biztosítási információkért kérjük, vegye fel a kapcsolatot a rendelővel."
                )
            ),
            "suggestions": T.get(
                "insurance_suggestions",
                []
            )
        }

    # ========================================================
    # APPOINTMENT STAGE 1: TREATMENT
    # ========================================================

    if stage == "awaiting_treatment":

        normalized_input = _normalize(raw)

        match = next(
            (
                (name, data)
                for name, data in clinic_data
                if _normalize(name) == normalized_input
            ),
            None
        )

        if not match:

            return {
                "reply": _text(
                    T,
                    "booking_question",
                    _localized(
                        language,
                        "Welche Behandlung möchten Sie buchen?",
                        "Which treatment would you like to book?",
                        "Milyen kezelésre szeretne időpontot foglalni?"
                    )
                ),
                "suggestions": treatment_names
            }

        name, data = match

        try:
            duration = int(
                data.get("duration") or 30
            )
        except (TypeError, ValueError):

            duration = 30

        if duration <= 0:
            duration = 30

        session.update({

            "treatment": name,

            "treat": name,

            "duration_minutes": duration,

            "stage": "awaiting_date"

        })

        return {
            "reply": _text(
                T,
                "which_date",
                _localized(
                    language,
                    "Bitte wählen Sie ein Datum.",
                    "Please choose a date.",
                    "Kérem, válasszon egy dátumot."
                )
            ),
            "suggestions": _date_suggestions(clinic)
        }

    # ========================================================
    # APPOINTMENT STAGE 2: DATE
    # ========================================================

    if stage == "awaiting_date":

        try:

            selected = datetime.strptime(
                raw,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            return {
                "reply": _localized(
                    language,
                    "Bitte geben Sie das Datum im Format YYYY-MM-DD ein.",
                    "Please enter the date in YYYY-MM-DD format, e.g. 2026-11-10.",
                    "Kérem, a dátumot ÉÉÉÉ-HH-NN formátumban adja meg, például: 2026-11-10."
                )
            }

        tz = ZoneInfo(
            clinic.get(
                "timezone",
                "Europe/Budapest"
            )
        )

        today = datetime.now(tz).date()

        if selected < today:

            return {
                "reply": _localized(
                    language,
                    "Bitte wählen Sie ein zukünftiges Datum.",
                    "Please choose a future date.",
                    "Kérem, válasszon egy jövőbeli dátumot."
                ),
                "suggestions": _date_suggestions(clinic)
            }

        duration = int(
            session.get(
                "duration_minutes",
                30
            )
        )

        # ----------------------------------------------------
        # GOOGLE CALENDAR AVAILABILITY
        # ----------------------------------------------------

        try:

            slots = get_available_slots(
                selected.isoformat(),
                clinic_id,
                duration
            )

            if slots is None:
                slots = []

        except Exception as exc:

            print(
                "\n"
                "========================================\n"
                "GOOGLE CALENDAR AVAILABILITY ERROR\n"
                "========================================\n"
                f"Clinic ID: {clinic_id}\n"
                f"Date: {selected.isoformat()}\n"
                f"Error: {repr(exc)}\n"
                "========================================",
                flush=True
            )

            traceback.print_exc()

            return {
                "reply": _localized(
                    language,
                    "Der Praxiskalender konnte momentan nicht überprüft werden. Bitte versuchen Sie es später erneut.",
                    "Sorry, I could not check this clinic's calendar. Please try again later or contact the clinic.",
                    "A rendelő naptárát jelenleg nem sikerült ellenőrizni. Kérjük, próbálja újra később, vagy vegye fel a kapcsolatot a rendelővel."
                )
            }

        # ----------------------------------------------------
        # NO AVAILABLE SLOTS
        # ----------------------------------------------------

        if not slots:

            return {
                "reply": _localized(
                    language,
                    "An diesem Tag sind leider keine Termine verfügbar. Bitte wählen Sie ein anderes Datum.",
                    "Sorry, there are no available appointments on this date. Please choose another date.",
                    "Sajnos ezen a napon nincs szabad időpont. Kérem, válasszon másik dátumot."
                ),
                "suggestions": _date_suggestions(clinic)
            }

        # ----------------------------------------------------
        # CREATE TIME MAP
        # ----------------------------------------------------

        slot_map = {}

        for slot in slots:

            try:

                start = datetime.fromisoformat(
                    slot["start"]
                )

                time_label = start.strftime(
                    "%H:%M"
                )

                slot_map[time_label] = slot["start"]

            except (
                KeyError,
                TypeError,
                ValueError
            ) as exc:

                print(
                    "Invalid calendar slot:",
                    repr(slot),
                    repr(exc),
                    flush=True
                )

        if not slot_map:

            return {
                "reply": _localized(
                    language,
                    "Die verfügbaren Termine konnten nicht gelesen werden. Bitte wählen Sie ein anderes Datum.",
                    "The available appointment times could not be read. Please choose another date.",
                    "A szabad időpontokat nem sikerült beolvasni. Kérem, válasszon másik dátumot."
                ),
                "suggestions": _date_suggestions(clinic)
            }

        session.update({

            "date": selected.isoformat(),

            "slot_map": slot_map,

            "stage": "awaiting_time"

        })

        return {
            "reply": (
                f"{_localized(language, 'Verfügbare Termine am', 'Available appointments on', 'Szabad időpontok ezen a napon')}"
                f" {selected.isoformat()}:"
            ),
            "suggestions": list(slot_map.keys())
        }

    # ========================================================
    # APPOINTMENT STAGE 3: TIME
    # ========================================================

    if stage == "awaiting_time":

        slot_map = session.get(
            "slot_map",
            {}
        )

        selected_time = raw.strip()

        if selected_time not in slot_map:

            return {
                "reply": _localized(
                    language,
                    "Diese Uhrzeit ist nicht verfügbar. Bitte wählen Sie eine der angezeigten Uhrzeiten.",
                    "This time is not available. Please select one of the available times.",
                    "Ez az időpont nem elérhető. Kérem, válasszon a megadott időpontok közül."
                ),
                "suggestions": list(slot_map.keys())
            }

        session.update({

            "time": selected_time,

            "start_time": slot_map[selected_time],

            "stage": "awaiting_name"

        })

        return {
            "reply": _text(
                T,
                "your_name",
                _localized(
                    language,
                    "Bitte geben Sie Ihren vollständigen Namen ein.",
                    "Please enter your full name.",
                    "Kérem, adja meg a teljes nevét."
                )
            )
        }

    # ========================================================
    # APPOINTMENT STAGE 4: NAME
    # ========================================================

    if stage == "awaiting_name":

        if len(raw) < 2:

            return {
                "reply": _localized(
                    language,
                    "Bitte geben Sie Ihren vollständigen Namen ein.",
                    "Please enter your full name.",
                    "Kérem, adja meg a teljes nevét."
                )
            }

        session.update({

            "name": raw,

            "stage": "awaiting_phone"

        })

        return {
            "reply": _text(
                T,
                "phone",
                _localized(
                    language,
                    "Bitte geben Sie Ihre Telefonnummer ein.",
                    "Please enter your phone number.",
                    "Kérem, adja meg a telefonszámát."
                )
            )
        }

    # ========================================================
    # APPOINTMENT STAGE 5: PHONE + BOOKING
    # ========================================================

    if stage == "awaiting_phone":

        phone_digits = re.sub(
            r"\D",
            "",
            raw
        )

        if len(phone_digits) < 5:

            return {
                "reply": _localized(
                    language,
                    "Bitte geben Sie eine gültige Telefonnummer ein.",
                    "Please enter a valid phone number.",
                    "Kérem, adjon meg egy érvényes telefonszámot."
                )
            }

        session["phone"] = raw

        # ----------------------------------------------------
        # CREATE GOOGLE CALENDAR EVENT
        # ----------------------------------------------------

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
                    session.get(
                        "duration_minutes",
                        30
                    )
                )
            )

            if not isinstance(result, dict):
                result = {}

        except Exception as exc:

            print(
                "\n"
                "========================================\n"
                "GOOGLE CALENDAR BOOKING ERROR\n"
                "========================================\n"
                f"Clinic ID: {clinic_id}\n"
                f"Patient: {session.get('name')}\n"
                f"Treatment: {session.get('treatment')}\n"
                f"Date: {session.get('date')}\n"
                f"Time: {session.get('time')}\n"
                f"Error: {repr(exc)}\n"
                "========================================",
                flush=True
            )

            traceback.print_exc()

            # Keep the patient's selected treatment.
            # Return to date selection so they can retry.
            session["stage"] = "awaiting_date"

            return {
                "reply": _localized(
                    language,
                    "Der Termin konnte leider nicht gebucht werden. Bitte versuchen Sie es erneut.",
                    "Sorry, the appointment could not be booked. Please try again.",
                    "Sajnos az időpont foglalása nem sikerült. Kérem, próbálja újra."
                ),
                "suggestions": _date_suggestions(clinic)
            }

        # ----------------------------------------------------
        # BOOKING CONFIRMED
        # ----------------------------------------------------

        confirmation = _text(
            T,
            "confirmation",
            _localized(
                language,
                "Termin bestätigt für {name}: {treatment}, {date} um {time}.",
                "Appointment confirmed for {name}: {treatment}, {date} at {time}.",
                "Időpont visszaigazolva: {name}, {treatment}, {date}, {time}."
            )
        ).format(
            name=session["name"],
            treatment=session.get(
                "treatment",
                "Consultation"
            ),
            date=session["date"],
            time=session["time"]
        )

        try:

            add_message(
                user_id,
                "assistant",
                confirmation
            )

        except Exception:

            print(
                "Could not save confirmation to memory.",
                flush=True
            )

            traceback.print_exc()

        event_link = result.get(
            "event_link"
        )

        # Clear completed booking session.
        session.clear()

        return {
            "reply": confirmation,
            "booking_confirmed": True,
            "event_link": event_link
        }

    # ========================================================
    # NORMAL INTENT HANDLING
    # ========================================================

    # Treatments question
    if _is_treatments_question(text):

        return {
            "reply": _text(
                T,
                "treatments_reply",
                "We offer the following treatments:"
            ),
            "suggestions": treatment_names
        }

    # Prices question
    if _is_prices_question(text):

        return {
            "reply": _price_reply(
                clinic_data,
                language
            ),
            "suggestions": treatment_names
        }

    # Insurance question
    if _is_insurance_question(text):

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

    # ========================================================
    # AI INTENT CLASSIFIER
    # ========================================================

    try:

        classified = classify_intent(
            user_id,
            text,
            language
        )

        if not isinstance(classified, dict):
            classified = {}

    except Exception as exc:

        print(
            "Intent classifier error:",
            repr(exc),
            flush=True
        )

        traceback.print_exc()

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

    try:

        confidence = float(
            classified.get(
                "confidence",
                0
            )
        )

    except (TypeError, ValueError):

        confidence = 0

    if confidence < 0.1:
        intent = "unknown"

    # --------------------------------------------------------
    # BOOKING
    # --------------------------------------------------------

    if intent == "booking":

        if not treatment_names:

            return {
                "reply": no_clinic_data(language)
            }

        session.clear()

        session["stage"] = "awaiting_treatment"

        return {
            "reply": _text(
                T,
                "booking_question",
                "Which treatment would you like to book?"
            ),
            "suggestions": treatment_names
        }

    # --------------------------------------------------------
    # PRICING OBJECTION
    # --------------------------------------------------------

    if intent == "pricing_objection":

        return {
            "reply": (
                _price_reply(
                    clinic_data,
                    language
                )
                if clinic_data
                else no_clinic_data(language)
            ),
            "suggestions": treatment_names
        }

    # --------------------------------------------------------
    # TREATMENTS
    # --------------------------------------------------------

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

    # ========================================================
    # OTHER INTENTS
    # ========================================================

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

    try:

        add_message(
            user_id,
            "assistant",
            reply
        )

    except Exception:

        print(
            "Could not save assistant message to memory.",
            flush=True
        )

        traceback.print_exc()

    response = {
        "reply": reply
    }

    suggestions_key = {
        "insurance": "insurance_suggestions"
    }.get(intent)

    if (
        suggestions_key
        and T.get(suggestions_key)
    ):

        response["suggestions"] = T[
            suggestions_key
        ]

    return response