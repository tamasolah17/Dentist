from intent_classifier import classify_intent
from memory import add_message
from flask import Flask, request, jsonify, session
from translations import TRANSLATIONS

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
        session["stage"] = "awaiting_appointment"

        return {
            "reply": T["morning_afternoon"],
            "suggestions": [
                T["morning"],
                T["afternoon"]
            ]
        }

    elif session.get("stage") == "awaiting_appointment":
        session["appointment"] = message
        session["stage"] = "awaiting_time"

        if message.lower() == T["morning"].lower():
            suggestions = ["9:00", "10:30", "11:30"]
        else:
            suggestions = ["12:30", "14:00", "15:30"]

        return {
            "reply": T["which_time"],
            "suggestions": suggestions
        }

    elif session.get("stage") == "awaiting_time":
        session["time"] = message
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
        session["phone"] = message
        session["stage"] = None

        confirmation = T["confirmation"].format(
            name=session["name"],
            treatment=session["treat"],
            date=session["appointment"],
            time=session["time"]
        )

        add_message(user_id, "assistant", confirmation)

        return {
            "reply": confirmation
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




        if "price" in message or "cost" in message:
            return {
                "reply": "🦷 Zahnaufhellung beginnt ab 120 € und die Beratung kostet 40 €.\n\nMöchten Sie einen Termin buchen?",
                "suggestions": ["Termin buchen", "Mit Mitarbeiter sprechen"]
            }

        if "insurance" in message:
            return {
                "reply": "Ja, wir akzeptieren die meisten gängigen Versicherungen.",
                "suggestions": ["Termin buchen", "Mit Rezeption sprechen"]
            }

    except Exception as e:
        print("Classifier error:", e)
        return {"reply": "Entschuldigung, das habe ich nicht verstanden. Können Sie es bitte anders formulieren?"}

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