from intent_classifier import classify_intent
from memory import add_message
from translations import TRANSLATIONS


def tr(language):
    return TRANSLATIONS.get(language, TRANSLATIONS["de"])


def handle_message(user_id, message, session, language):

    T = tr(language)

    raw_message = message.strip()
    message = raw_message.lower()

    # =====================================
    # 1. TREATMENT SELECTION
    # =====================================

    treatment_map = {
        treatment.lower(): treatment
        for treatment in T["treatments"]
    }

    if message in treatment_map:

        selected_treatment = treatment_map[message]

        session["selected_treatment"] = selected_treatment
        session["stage"] = "awaiting_treatment"
        session["behandlung"] = selected_treatment
        session["treat"] = selected_treatment

        return {
            "reply": T["great_choice"].format(
                treatment=selected_treatment
            ),
            "suggestions": [
                T["book"],
                T["human"]
            ]
        }

    # =====================================
    # 2. APPOINTMENT FLOW
    # =====================================

    if session.get("stage") == "awaiting_treatment":

        session["behandlung"] = raw_message
        session["treatment"] = raw_message
        session["stage"] = "awaiting_date"

        return {
            "reply": T["which_date"],
            "suggestions": [
                T["tomorrow"],
                T["this_week"],
                T["next_week"]
            ]
        }

    elif session.get("stage") == "awaiting_date":

        session["date"] = raw_message
        session["stage"] = "awaiting_appointment"

        return {
            "reply": T["morning_afternoon"],
            "suggestions": [
                T["morning"],
                T["afternoon"]
            ]
        }

    elif session.get("stage") == "awaiting_appointment":

        session["appointment"] = raw_message
        session["stage"] = "awaiting_time"

        if message == T["morning"].lower():

            suggestions = [
                "9:00",
                "10:30",
                "11:30"
            ]

        else:

            suggestions = [
                "12:30",
                "14:00",
                "15:30"
            ]

        return {
            "reply": T["which_time"],
            "suggestions": suggestions
        }

    elif session.get("stage") == "awaiting_time":

        session["time"] = raw_message
        session["stage"] = "awaiting_name"

        return {
            "reply": T["your_name"]
        }

    elif session.get("stage") == "awaiting_name":

        session["name"] = raw_message
        session["stage"] = "awaiting_phone"

        return {
            "reply": T["phone"]
        }

    elif session.get("stage") == "awaiting_phone":

        session["phone"] = raw_message
        session["stage"] = None

        confirmation = T["confirmation"].format(
            name=session["name"],
            treatment=session["treat"],
            date=session["date"],
            time=session["time"]
        )

        add_message(
            user_id,
            "assistant",
            confirmation
        )

        return {
            "reply": confirmation
        }

    # =====================================
    # 3. EMPTY MESSAGE
    # =====================================

    if not message:

        return {
            "reply": T["how_can_i_help"],
            "suggestions": T["main_suggestions"]
        }

    # =====================================
    # 4. SIMPLE KEYWORD HANDLING
    # =====================================

    if language == "de":

        if "behandlung" in message:

            return {
                "reply": T["treatments_reply"],
                "suggestions": T["treatments"]
            }

        if "preis" in message or "kosten" in message:

            return {
                "reply": T["pricing_reply"],
                "suggestions": T["pricing_suggestions"]
            }

        if "versicherung" in message:

            return {
                "reply": T["insurance_reply"],
                "suggestions": T["insurance_suggestions"]
            }

    elif language == "en":

        if "treatment" in message:

            return {
                "reply": T["treatments_reply"],
                "suggestions": T["treatments"]
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

    elif language == "hun":

        if "kezelés" in message or "kezelések" in message:

            return {
                "reply": T["treatments_reply"],
                "suggestions": T["treatments"]
            }

        if "ár" in message or "árak" in message or "költség" in message:

            return {
                "reply": T["pricing_reply"],
                "suggestions": T["pricing_suggestions"]
            }

        if "biztosítás" in message:

            return {
                "reply": T["insurance_reply"],
                "suggestions": T["insurance_suggestions"]
            }

    # =====================================
    # 5. AI INTENT CLASSIFIER
    # =====================================

    result = classify_intent(
        user_id,
        message,
        language
    )

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

        return {
            "reply": T["pricing_reply"],
            "suggestions": T["pricing_suggestions"]
        }

    elif intent == "treatments":

        return {
            "reply": T["treatments_reply"],
            "suggestions": T["treatments"]
        }

    elif intent == "emergency":

        return {
            "reply": T["emergency_reply"]
        }

    elif intent == "insurance":

        return {
            "reply": T["insurance_reply"],
            "suggestions": T["insurance_suggestions"]
        }

    elif intent == "Location_Hours":

        reply = T["location_reply"]

    elif intent == "Human":

        reply = T["human_reply"]

    elif intent == "welcome_message":

        reply = T["welcome"]

    else:

        reply = T["unknown_reply"]

    add_message(
        user_id,
        "assistant",
        reply
    )

    return {
        "reply": reply
    }