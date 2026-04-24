from intent_classifier import classify_intent
from memory import add_message
from flask import Flask, request, jsonify, session


def handle_message(user_id, message, session):
    # =========================
    # TREATMENT SELECTION FLOW
    # =========================

    treatments = ["whitening", "implants", "braces", "cleanings"]
    raw_message = message.strip()
    message = raw_message.lower()
    if message.lower() in treatments:
        session["selected_treatment"] = message.capitalize()
        session["stage"] = "awaiting_treatment"
        return {
            "reply": (
                f"Gute Wahl! 🦷 {message.capitalize()} gehört zu unseren häufigsten Behandlungen.\n\n"
                "Möchten Sie einen Termin buchen oder mit unserem Team sprechen?"
            ),
            "suggestions": [
                "Termin buchen",
                "Mit Mitarbeiter sprechen"
            ]
        }

    # =========================
    # APPOINTMENT FLOW HANDLER
    # =========================

    if session.get("stage") == "awaiting_treatment":
        session["treatment"] = message
        session["stage"] = "awaiting_date"

        return {
            "reply": "Welcher Termin passt Ihnen am besten?",
            "suggestions": ["Morgen", "Diese Woche", "Nächste Woche"]
        }

    elif session.get("stage") == "awaiting_date":
        session["date"] = message
        session["stage"] = "awaiting_appointment"

        return {
            "reply": "Bevorzugen Sie einen Termin am Vormittag oder Nachmittag?",
            "suggestions": ["Vormittag", "Nachmittag"]
        }

    elif session.get("stage") == "awaiting_appointment":
        session["appointment"] = message
        session["stage"] = "awaiting_time"
        choice = message.strip().lower()

        if choice == "vormittag":
            suggestions = ["9:00", "10:30", "11:30"]
        else:
            suggestions = ["12:30", "14:00", "15:30"]

        return {
            "reply": "Welche Uhrzeit passt Ihnen am besten?",
            "suggestions": suggestions
        }

    elif session.get("stage") == "awaiting_time":
        session["time"] = message
        session["stage"] = "awaiting_name"

        return {
            "reply": "Wie ist Ihr vollständiger Name?"
        }

    elif session.get("stage") == "awaiting_name":
        session["name"] = raw_message
        session["stage"] = "awaiting_phone"

        return {
            "reply": "📞 Bitte geben Sie Ihre Telefonnummer an, damit wir den Termin bestätigen können."
        }

    elif session.get("stage") == "awaiting_phone":
        session["phone"] = message
        session["stage"] = None

        confirmation = (
            f"✅ Vielen Dank, {session['name']}!<br><br>"
            "🗓️ Ihre Terminanfrage im Überblick:<br><br>"
            f"• Behandlung: {session['selected_treatment']}<br>"
            f"• Datum: {session['appointment']}<br>"
            f"• Uhrzeit: {session['time']}<br><br>"
            "📞 Unser Team wird sich in Kürze bei Ihnen melden, um den Termin zu bestätigen."
        )

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

    if confidence < 0.1:
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