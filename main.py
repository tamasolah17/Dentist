"""Flask entry point. Every widget request must include its clinic_id."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from translations import TRANSLATIONS
from agent import handle_message
from clinics import (
    CLINICS,
    get_clinic,
    clinic_exists,
    save_clinic,
    list_clinic_ids,
    DB_PATH,
)
from google_auth import google_auth
from clinic_admin import create_admin_blueprint


app2 = Flask(__name__)
app2.secret_key = os.getenv("FLASK_SECRET_KEY")

if not app2.secret_key:
    raise RuntimeError(
        "FLASK_SECRET_KEY is missing. Set a long, random secret in the environment."
    )

CORS(
    app2,
    resources={
        r"/chat": {"origins": "*"},
        r"/clinic-config": {"origins": "*"},
    },
    allow_headers=["Content-Type", "X-Admin-Key"],
    methods=["GET", "POST", "OPTIONS"],
)

app2.register_blueprint(google_auth)
app2.register_blueprint(
    create_admin_blueprint(
        get_clinic,
        save_clinic,
        DB_PATH,
    )
)

user_sessions = {}


def _clinic_name(clinic):
    """Support both the new clinic_name field and older name field."""
    if not isinstance(clinic, dict):
        return ""
    return str(
        clinic.get("clinic_name")
        or clinic.get("name")
        or clinic.get("practice_name")
        or ""
    ).strip()


def _google_place_details(place_id):
    """
    Fetch current Google Place details using Places API (New).
    The API key stays on the server and is never sent to the widget.
    """
    api_key = (
        os.getenv("GOOGLE_MAPS_API_KEY")
        or os.getenv("GOOGLE_PLACES_API_KEY")
    )

    if not api_key or not place_id:
        return None

    url = (
        "https://places.googleapis.com/v1/places/"
        + quote(str(place_id).strip(), safe="")
    )

    req = Request(
        url,
        headers={
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": (
                "id,displayName,rating,userRatingCount,googleMapsUri"
            ),
        },
        method="GET",
    )

    try:
        with urlopen(req, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))

        display_name = payload.get("displayName") or {}
        return {
            "place_id": payload.get("id") or place_id,
            "clinic_name": display_name.get("text") or "",
            "google_rating": payload.get("rating"),
            "google_review_count": payload.get("userRatingCount"),
            "google_maps_uri": payload.get("googleMapsUri") or "",
            "google_verified": True,
        }

    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        app2.logger.warning(
            "Google Places lookup failed for Place ID %s: %s",
            place_id,
            exc,
        )
        return None


@app2.route("/clinic-config", methods=["GET", "OPTIONS"])
def clinic_config():
    """Public, read-only widget configuration for one clinic."""
    if request.method == "OPTIONS":
        return "", 204

    clinic_id = str(request.args.get("clinic_id", "")).strip()

    if not clinic_id:
        return jsonify({"error": "clinic_id is required"}), 400

    if not clinic_exists(clinic_id):
        return jsonify({"error": "Unknown clinic_id"}), 404

    clinic = get_clinic(clinic_id) or {}
    if not isinstance(clinic, dict):
        app2.logger.error("Invalid clinic configuration for %s", clinic_id)
        return jsonify({"error": "Invalid clinic configuration"}), 500

    # Support common field names while keeping the existing clinic store intact.
    google_config = clinic.get("google")
    if not isinstance(google_config, dict):
        google_config = {}

    place_id = (
        clinic.get("google_place_id")
        or clinic.get("place_id")
        or google_config.get("place_id")
    )

    maps_url = (
        clinic.get("google_maps_url")
        or clinic.get("google_maps_uri")
        or ""
    )

    result = {
        "clinic_id": clinic_id,
        "clinic_name": _clinic_name(clinic),
        "google_rating": None,
        "google_review_count": None,
        "google_maps_uri": maps_url,
        "google_verified": False,
    }

    # Always prefer fresh Google data over values manually entered in Excel.
    google_data = _google_place_details(place_id)

    if google_data:
        result.update(google_data)

        # Prefer the clinic's configured name; Google displayName is a fallback.
        result["clinic_name"] = (
            _clinic_name(clinic)
            or google_data.get("clinic_name")
            or ""
        )

        # If Google returned a Maps URI, use it instead of a manually supplied URL.
        result["google_maps_uri"] = (
            google_data.get("google_maps_uri")
            or maps_url
        )

    return jsonify(result)


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

    clinic = get_clinic(clinic_id) or {}

    if not message:
        welcome = TRANSLATIONS.get(
            language,
            TRANSLATIONS["de"]
        ).get("welcome", "How can I help you?")

        return jsonify({
            "intent": "welcome_message",
            "confidence": 1.0,
            "reply": welcome,
            "clinic_name": _clinic_name(clinic),
        })

    try:
        result = handle_message(
            session_id,
            message,
            session,
            language,
            clinic,
            clinic_id,
        )

        # Include clinic identity as response metadata without changing
        # the booking conversation or Google Calendar workflow.
        if isinstance(result, dict):
            result.setdefault("clinic_name", _clinic_name(clinic))

        return jsonify(result)

    except Exception:
        app2.logger.exception(
            "Chat request failed for %s",
            clinic_id,
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