from intent_classifier import classify_intent
from memory import add_message
from flask import Flask, request, jsonify, session


def handle_message(user_id, message, session):
    # =========================
    # TREATMENT SELECTION FLOW
    # =========================

    treatments = ["whitening", "implants", "braces", "cleanings"]
    message = message.lower().strip()
    if message.lower() in treatments:
        session["selected_treatment"] = message.capitalize()
        session["stage"] = "awaiting_treatment"
        return {
            "reply": (
                f"Great choice! 🦷 {message.capitalize()} is one of our most requested treatments.\n\n"
                "Would you like to book an appointment or speak with our receptionist?"
            ),
            "suggestions": [
                "Book appointment",
                "Talk to human"
            ]
        }
    # =========================
    # APPOINTMENT FLOW HANDLER
    # =========================

    if session.get("stage") == "awaiting_treatment":
        session["treatment"] = message
        session["stage"] = "awaiting_date"

        return {
            "reply": "📅 What date works best for you?",
            "suggestions": ["Tomorrow", "This week", "Next week"]
        }

    elif session.get("stage") == "awaiting_date":
        session["date"] = message
        session["stage"] = "awaiting_time"

        return {
            "reply": "⏰ Do you prefer morning or afternoon?",
            "suggestions": ["Morning", "Afternoon"]
        }

    elif session.get("stage") == "awaiting_time":
        session["time"] = message
        session["stage"] = "awaiting_name"

        return {
            "reply": "👤 Could I have your full name please?"
        }

    elif session.get("stage") == "awaiting_name":
        session["name"] = message
        session["stage"] = "awaiting_phone"

        return {
            "reply": "📞 Please provide your phone number so we can confirm the appointment."
        }

    elif session.get("stage") == "awaiting_phone":
        session["phone"] = message
        session["stage"] = None

        confirmation = (
            f"✅ Thank you {session['name']}!\n\n"
            f"Appointment request received:\n"
            f"Treatment: {session['treatment']}\n"
            f"Date: {session['date']}\n"
            f"Time: {session['time']}\n\n"
            "Our receptionist will contact you shortly."
        )

        add_message(user_id, "assistant", confirmation)

        return {"reply": confirmation}

    # =========================
    # NORMAL INTENT HANDLING
    # =========================
    if not message:
        return {
            "reply": "ANYÁTOKAT MAGYAROK",
            "suggestions": [
                "Book appointment",
                "Treatments",
                "Insurance",
                "Emergency"
            ]
        }
    try:
        if "treatment" in message:
            return {
                "reply": "We offer whitening, implants, braces and cleanings. Which are you interested in?",
                "suggestions": ["whitening", "implants", "braces", "cleanings"]
            }

        if "price" in message or "cost" in message:
            return {
                "reply": "🦷 Teeth whitening starts at $120 and consultation is $40.\n\nWould you like to book an appointment?",
                "suggestions": ["Book appointment", "Talk to human"]
            }

        if "insurance" in message:
            return {
                "reply": "Yes, we accept most major insurance providers.",
                "suggestions": ["Book appointment", "Talk to receptionist"]
            }
        result = classify_intent(user_id, message)
        print("DEBUG INTENT:", result)


    except Exception as e:
        print("Classifier error:", e)
        return {"reply": "Sorry, I didn't understand that. Could you rephrase?"}

    intent = result["intent"].lower()
    confidence = result["confidence"].lower()


    if confidence < 0.1:
        intent = "unknown"

    if intent == "Booking":
        session["stage"] = "awaiting_treatment"

        return {
            "reply": "🦷 What treatment would you like to book?",
            "suggestions": [
                "Teeth Cleaning",
                "Teeth Whitening",
                "Dental Implant",
                "General Check-up"
            ]
        }


    elif intent == "pricing_objection":

        return {
            "reply": (

                "🦷 Teeth whitening starts at $120 and consultation is $40.\n\n"
                "Would you like to book an appointment for a detailed quote?"

            ),
            "suggestions": [

                "Book appointment",
                "Talk to a human"

            ]

        }
    elif intent == "Treatments":

        return {
            "reply": (

                "We offer whitening, implants, braces and cleanings. Which are you interested in?"


            ),
            "suggestions": [
                "whitening",
                "implants",
                "braces",
                "cleanings"

            ]

        }

    elif intent == "Emergency":
        reply = "🚨 Please call us immediately for emergencies. Would you like the number?"


    elif intent == "Insurance":

        return {

            "reply": (

                "Yes, we accept most major insurance providers.\n\n"
                "Would you like to book a consultation so we can verify your coverage?"

            ),

            "suggestions": [

                "Book appointment",
                "Talk to receptionist"

            ]

        }
    elif intent == "Location_Hours":
        reply = "📍 123 Main Street. Mon–Fri 9am–6pm."

    elif intent == "Human":
        reply = "Please leave your name and phone number and we’ll call you."

    elif intent == "welcome_message":
        reply =  "Hi 👋 Welcome to our clinic. My name is Lena, your personal Assistant. How can I help you?:)."

    else:
        reply = "I can help with appointments, treatments, insurance, or emergencies."

    add_message(user_id, "assistant", reply)

    return {"reply": reply}
