from intent_classifier import classify_intent
from memory import add_message
from flask import Flask, request, jsonify, session


def handle_message(user_id, message, session):
    treatments = ["whitening", "implants", "braces", "cleanings"]

    TREATMENT_LABELS = {
        "cleanings": "Zahnreinigung",
        "whitening": "Zahnaufhellung",
        "implants": "Implantat",
        "braces": "Zahnspange"
    }

    raw_message = message.strip()
    message = raw_message.lower()

    # =========================
    # START BOOKING FLOW
    # =========================
    if message == "termin buchen":
        session.clear()
        session["stage"] = "awaiting_treatment"

        return {
            "reply": "🦷 Welche Behandlung möchten Sie buchen?",
            "suggestions": ["cleanings", "whitening", "implants", "braces"]
        }

    # =========================
    # TREATMENT SELECTION (SAFE)
    # =========================
    if (
        message in treatments
        and session.get("stage") == "awaiting_treatment"
    ):
        session["selected_treatment"] = TREATMENT_LABELS.get(message, message)
        session["stage"] = "awaiting_date"

        return {
            "reply": (
                f"Gute Wahl! 🦷 {session['selected_treatment']} ist eine sehr gefragte Behandlung.\n\n"
                "📅 Welcher Termin passt Ihnen am besten?"
            ),
            "suggestions": ["Morgen", "Diese Woche", "Nächste Woche"]
        }

    # =========================
    # APPOINTMENT FLOW HANDLER
    # =========================

    if (
            message in treatments
            and session.get("stage") == "awaiting_treatment"
    ):
        session["selected_treatment"] = TREATMENT_LABELS.get(message, message)
        session["stage"] = "awaiting_date"

        return {
            "reply": (
                f"Gute Wahl! 🦷 {session['selected_treatment']} ist eine sehr gefragte Behandlung.\n\n"
                "📅 Welcher Termin passt Ihnen am besten?"
            ),
            "suggestions": ["Morgen", "Diese Woche", "Nächste Woche"]
        }

        # =========================
        # DATE
        # =========================
    elif session.get("stage") == "awaiting_date":
        session["date"] = raw_message
        session["stage"] = "awaiting_appointment"

        return {
            "reply": "Bevorzugen Sie einen Termin am Vormittag oder Nachmittag?",
            "suggestions": ["Vormittag", "Nachmittag"]
        }

        # =========================
        # TIME PERIOD
        # =========================
    elif session.get("stage") == "awaiting_appointment":
        session["appointment"] = raw_message
        session["stage"] = "awaiting_time"

        if message == "vormittag":
            suggestions = ["9:00", "10:30", "11:30"]
        else:
            suggestions = ["12:30", "14:00", "15:30"]

        return {
            "reply": "Welche Uhrzeit passt Ihnen am besten?",
            "suggestions": suggestions
        }

        # =========================
        # TIME
        # =========================
    elif session.get("stage") == "awaiting_time":
        session["time"] = raw_message
        session["stage"] = "awaiting_name"

        return {
            "reply": "👤 Wie ist Ihr vollständiger Name?"
        }

        # =========================
        # NAME
        # =========================
    elif session.get("stage") == "awaiting_name":
        session["name"] = raw_message
        session["stage"] = "awaiting_phone"

        return {
            "reply": "📞 Bitte geben Sie Ihre Telefonnummer an, damit wir den Termin bestätigen können."
        }

        # =========================
        # PHONE + CONFIRMATION
        # =========================
    elif session.get("stage") == "awaiting_phone":
        session["phone"] = raw_message
        session["stage"] = None

        confirmation = (
            f"✅ Vielen Dank, {session['name']}!<br><br>"
            "🗓️ Ihre Terminanfrage im Überblick:<br><br>"
            f"• Behandlung: {session.get('selected_treatment', '—')}<br>"
            f"• Datum: {session.get('date', '—')}<br>"
            f"• Tageszeit: {session.get('appointment', '—')}<br>"
            f"• Uhrzeit: {session.get('time', '—')}<br><br>"
            "📞 Wir prüfen kurz die Verfügbarkeit und bestätigen den Termin in wenigen Minuten."
        )

        return {"reply": confirmation}

        add_message(user_id, "assistant", confirmation)

        return {"reply": confirmation}

    # =========================
    # NORMAL INTENT HANDLING
    # =========================
    if not message:
        return {
            "reply": "Wie kann ich Ihnen helfen?",
            "suggestions": [
                "Termin buchen",
                "Behandlungen",
                "Versicherung",
                "Notfall"
            ]
        }

    try:
        if "treatment" in message:
            return {
                "reply": "Wir bieten Zahnaufhellung, Implantate, Zahnspangen und Zahnreinigung an. Wofür interessieren Sie sich?",
                "suggestions": ["whitening", "implants", "braces", "cleanings"]
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

    result = classify_intent(user_id, message)
    intent = result["intent"]
    confidence = result["confidence"]
    print("DEBUG INTENT:", result)

    if confidence < 0.25:
        intent = "unknown"

    if intent == "booking":
        session["stage"] = "awaiting_treatment"

        return {
            "reply": "🦷 Welche Behandlung möchten Sie buchen?",
            "suggestions": [
                "Zahnreinigung",
                "Zahnaufhellung",
                "Implantat",
                "Kontrolluntersuchung"
            ]
        }

    elif intent == "pricing_objection":

        return {
            "reply": (
                "🦷 Zahnaufhellung beginnt ab 120 € und die Beratung kostet 40 €.\n\n"
                "Möchten Sie einen Termin für ein genaues Angebot buchen?"
            ),
            "suggestions": [
                "Termin buchen",
                "Mit Mitarbeiter sprechen"
            ]
        }

    elif intent == "treatments":

        return {
            "reply": (
                "Wir bieten Zahnaufhellung, Implantate, Zahnspangen und Zahnreinigung an. Wofür interessieren Sie sich?"
            ),
            "suggestions": [
                "whitening",
                "implants",
                "braces",
                "cleanings"
            ]
        }

    elif intent == "emergency":

        return {
            "reply": "🚨 Bitte rufen Sie uns im Notfall direkt an. Möchten Sie unsere Telefonnummer?"
        }

    elif intent == "insurance":

        return {
            "reply": (
                "Ja, wir akzeptieren die meisten gängigen Versicherungen.\n\n"
                "Möchten Sie einen Termin vereinbaren, damit wir Ihre Versicherung prüfen können?"
            ),
            "suggestions": [
                "Termin buchen",
                "Mit Rezeption sprechen"
            ]
        }

    elif intent == "Location_Hours":
        reply = "📍 Musterstraße 123. Mo–Fr 9:00–18:00 Uhr."

    elif intent == "Human":
        reply = "Bitte hinterlassen Sie Ihren Namen und Ihre Telefonnummer, wir rufen Sie zurück."

    elif intent == "welcome_message":
        reply = "Guten Tag 👋 Willkommen in unserer Praxis. Ich bin Ihr digitaler Assistent. Wie kann ich Ihnen helfen?"

    else:
        reply = "Ich kann Ihnen bei Terminen, Behandlungen, Versicherungen oder Notfällen helfen."

    add_message(user_id, "assistant", reply)
    print("l")

    return {"reply": reply}