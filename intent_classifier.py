# intent_classifier.py
import json
import os
from openai import OpenAI
from memory import get_history, add_message

SYSTEM_PROMPT = """
You are a conversion-focused sales assistant for an e-commerce website.

Your goal:
- Help hesitant visitors make a confident purchase decision
- Reduce doubt, friction, and uncertainty
- Increase checkout conversion

Classify the user's message into exactly ONE intent.


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

Guidelines:
- Questions about insurance and other discounts from patients → insurance
- Questions about treatments → treatments
- Questions about teeth issues, side effects → issues
- Questions about bookings → booking
- Questions about emergency appointments → emergency
- Questions about price, discounts, value → pricing_objection
- Questions about legitimacy, reviews, trust → trust_objection
- If the chatbox is blank, contains 0 answers and 0 questions → trigger welcome_message

   
    
   
- Clear buying signals → checkout_intent
- Requests for a human → human
- Unclear intent → unknown

Return JSON only. No explanations.

Format:
{
  "intent": "<intent>",
  "confidence": 0.0-1.0
}
"""




def classify_intent(user_id: str, message: str) -> dict:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    history = get_history(user_id)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": message}
    ]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0,

    )

    raw = response.choices[0].message.content.strip()
    print("RAW OPENAI RESPONSE:", raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {"intent": "unknown", "confidence": 0.0}

    # store user message in memory
    add_message(user_id, "user", message)

    return data
