"""Flask entry point. Every widget request must include its clinic_id."""

import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from translations import TRANSLATIONS
from agent import handle_message
from clinics import CLINICS, get_clinic, clinic_exists, save_clinic, list_clinic_ids
from google_auth import google_auth

app2 = Flask(__name__)
app2.secret_key = os.getenv("FLASK_SECRET_KEY")

if not app2.secret_key:
    raise RuntimeError(
        "FLASK_SECRET_KEY is missing. Set a long, random secret in the environment."
    )

CORS(app2)
app2.register_blueprint(google_auth)

user_sessions = {}


@app2.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True) or {}

    user_id = str(data.get("user_id", "")).strip()
    clinic_id = str(data.get("clinic_id", "")).strip()
    message = str(data.get("message", "")).strip()
    language = str(data.get("language", "de")).lower()

    if not user_id or not clinic_id:
        return jsonify({
            "error": "clinic_id and user_id are required"
        }), 400

    if not clinic_exists(clinic_id):
        return jsonify({
            "error": "Unknown clinic_id"
        }), 404

    if language not in TRANSLATIONS:
        language = "de"

    # Every clinic gets a separate user session.
    session_id = f"{clinic_id}:{user_id}"
    session = user_sessions.setdefault(session_id, {})

    if not message:
        welcome = TRANSLATIONS.get(
            language,
            TRANSLATIONS["de"]
        ).get("welcome", "How can I help you?")

        return jsonify({
            "intent": "welcome_message",
            "confidence": 1.0,
            "reply": welcome
        })

    try:
        result = handle_message(
            session_id,
            message,
            session,
            language,
            get_clinic(clinic_id),
            clinic_id
        )

        return jsonify(result)

    except Exception:
        app2.logger.exception(
            "Chat request failed for %s",
            clinic_id
        )

        return jsonify({
            "error": "Internal chat error"
        }), 500


@app2.route("/admin/clinics", methods=["POST"])
def create_or_update_clinic():

    expected_key = os.getenv("ADMIN_API_KEY")
    supplied_key = request.headers.get("X-Admin-Key", "")

    if not expected_key or supplied_key != expected_key:
        return jsonify({
            "error": "Unauthorized"
        }), 401

    data = request.get_json(silent=True) or {}

    clinic_id = str(data.get("clinic_id", "")).strip()
    config = data.get("config")

    if not isinstance(config, dict):
        return jsonify({
            "error": "config must be a JSON object"
        }), 400

    try:
        save_clinic(clinic_id, config)

        return jsonify({
            "status": "saved",
            "clinic_id": clinic_id,
            "next_step": (
                f"Connect Google Calendar at "
                f"/google/login?clinic_id={clinic_id}"
            )
        }), 201

    except ValueError as exc:
        return jsonify({
            "error": str(exc)
        }), 400


@app2.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "configured_clinics": list_clinic_ids()
    })


@app2.route("/")
def index():
    return render_template("dentistpage.html")


if __name__ == "__main__":
    app2.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000"))
    )