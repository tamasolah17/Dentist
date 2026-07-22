# intent_classifier.py
import json
import os
from openai import OpenAI
from memory import get_history, add_message

SYSTEM_PROMPT = """
Du bist ein konversionsorientierter digitaler Assistent für eine Zahnarztpraxis.

Dein Ziel:
- Patienten bei der Terminvereinbarung unterstützen
- Unsicherheiten reduzieren und Vertrauen aufbauen
- Mehr Anfragen in konkrete Termine umwandeln

Klassifiziere die Nachricht des Nutzers in genau EINE Intent-Kategorie.


ALLOWED_INTENTS = [
    "pricing_objection",
    "trust_objection",
    "welcome_message",
    "insurance",
    "treatments",
    "booking",
    "emergency",
    "issues",
    "human",
    "unknown"
]

Richtlinien:
- Fragen zu Versicherungen oder Kostenübernahme → insurance

- Questions, which include "treatments" or "Behandlungen" or "kezelés" → treatments
- Fragen zu Zahnbeschwerden, Schmerzen oder Nebenwirkungen → issues
- Fragen zur Terminvereinbarung → booking
- Notfälle oder dringende Schmerzen → emergency
- Fragen zu Preisen oder Kosten → pricing_objection
- Fragen zu Vertrauen, Bewertungen oder Seriosität → trust_objection
- Wenn keine Nachricht vorhanden ist → welcome_message

- Wunsch nach persönlichem Kontakt → human
- Unklare Anfrage → unknown

Gib ausschließlich JSON zurück. Keine Erklärungen.

Format:
{
  "intent": "<intent>",
  "confidence": 0.0-1.0
}
"""




def classify_intent(user_id: str, message: str, language: str = "de") -> dict:

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    history = get_history(user_id)

    if language == "en":
        system_prompt = """
        You are a conversion-focused digital assistant for a dental clinic.

        Your goal:
        - Help patients book appointments
        - Reduce uncertainty and build trust
        - Convert inquiries into bookings

        Classify the user message into EXACTLY ONE intent category.

        ALLOWED_INTENTS = [
            "pricing_objection",
            "trust_objection",
            "welcome_message",
            "insurance",
            "treatments",
            "booking",
            "emergency",
            "issues",
            "human",
            "unknown"
        ]

        Return ONLY JSON.

        Format:
        {
          "intent": "<intent>",
          "confidence": 0.0-1.0
        }
        """
    else:
        system_prompt = SYSTEM_PROMPT

    messages = [
        {"role": "system", "content": system_prompt},
        *history,
        {"role": "user", "content": message}
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0,
        response_format={"type": "json_object"}
    )

    raw = response.choices[0].message.content.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"intent": "unknown", "confidence": 0.0}

    add_message(user_id, "user", message)

    return data
