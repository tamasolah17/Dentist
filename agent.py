from intent_classifier import classify_intent
from memory import add_message
from flask import Flask, request, jsonify, session
from translations import TRANSLATIONS
from calendar_demo import get_available_slots, book_slot

def tr(language):
    return TRANSLATIONS.get(language, TRANSLATIONS["de"])
temp = ""
def handle_message(user_id, message, session,language):
    # =========================
    # TREATMENT SELECTION FLOW
    # =========================
    T = tr(language)

    raw_message = message.strip()
    message = raw_message.lower()

    # =========================
    # TREATMENT SELECTION FLOW
    # =========================

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
            "suggestions": [
                T["tomorrow"],
                T["this_week"],
                T["next_week"]
            ]
        }


    # =========================
    # APPOINTMENT FLOW HANDLER
    # =========================

    # =========================
    # APPOINTMENT FLOW HANDLER
    # =========================

    if session.get("stage") == "awaiting_treatment":
        session["behandlung"] = message
        session["treatment"] = message
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

        session["date"] = message

        available_slots = get_available_slots(message)

        if available_slots is None:
            return {

                "reply": "Please enter the date in YYYY-MM-DD format. Example: 2026-11-10"

            }

        if not available_slots:
            return {

                "reply": "Sorry, there are no available appointments on this date. Please choose another date."

            }

        session["available_slots"] = available_slots

        session["stage"] = "awaiting_time"

        return {

            "reply": f"Available appointments on {message}:",

            "suggestions": available_slots

        }

   


    elif session.get("stage") == "awaiting_time":

        selected_time = message.strip()

        if selected_time not in session.get("available_slots", []):
            return {

                "reply": "This time is not available. Please select one of the available times.",

                "suggestions": session.get("available_slots", [])

            }

        session["time"] = selected_time

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

        success = book_slot(

            date_text=session["date"],

            time_text=session["time"],

            user_id=user_id,

            name=session["name"],

            phone=session["phone"],

            treatment=session.get("treat", session.get("treatment", "Consultation"))

        )

        if not success:
            session["stage"] = "awaiting_date"

            return {

                "reply": "Sorry, this appointment is no longer available. Please select another date."

            }

        session["stage"] = None

        confirmation = T["confirmation"].format(

            name=session["name"],

            treatment=session.get("treat", session.get("treatment", "Consultation")),

            date=session["date"],

            time=session["time"]

        )

        add_message(user_id, "assistant", confirmation)

        return {

            "reply": confirmation,

            "booking_confirmed": True

        }

    # =========================
    # NORMAL INTENT HANDLING
    # =========================
    if not message:
        return {
            "reply": T["how_can_i_help"],
            "suggestions": T["main_suggestions"]
        }

    try:
        if (
                "treatment" in message
                or "treatments" in message
                or "behandlungen" in message
                or "kezelés" in message
                or "kezelések" in message
        ):
            print("🔥 TREATMENT MATCHED")

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

    except Exception as e:
        print("Classifier error:", e)
        return {
            "reply": T["error_reply"]
        }




        

    result = classify_intent(user_id, message,language)
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

    add_message(user_id, "assistant", reply)
    print("l")

    return {"reply": reply}