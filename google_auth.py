
import os
import json

from pathlib import Path
from flask import Blueprint, redirect, request, session, jsonify
from google_auth_oauthlib.flow import Flow

google_auth = Blueprint("google_auth", __name__)

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events.freebusy",
    "https://www.googleapis.com/auth/calendar.events.owned",
]

REDIRECT_URI = "http://localhost:5000/google/callback"

TOKEN_PATH = Path(__file__).parent / "instance" / "google_token.json"


def get_client_config():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError("Google OAuth environment variables are missing")

    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    }


@google_auth.route("/google/login")
def google_login():
    flow = Flow.from_client_config(
        get_client_config(),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        code_challenge_method="S256"
    )

    session["google_code_verifier"] = flow.code_verifier


    session["google_oauth_state"] = state

    return redirect(authorization_url)


@google_auth.route("/google/callback")
def google_callback():
    saved_state = session.get("google_oauth_state")
    returned_state = request.args.get("state")

    if not saved_state or saved_state != returned_state:
        return jsonify({"error": "Invalid OAuth state"}), 400

    if request.args.get("error"):
        return jsonify({
            "error": "Google authorization failed",
            "details": request.args.get("error")
        }), 400

    code = request.args.get("code")

    if not code:
        return jsonify({"error": "Authorization code missing"}), 400

    code_verifier = session.get("google_code_verifier")

    if not code_verifier:
        return jsonify({
            "error": "Missing PKCE code verifier. Please restart Google login."
        }), 400

    flow = Flow.from_client_config(
        get_client_config(),
        scopes=SCOPES,
        state=saved_state,
        redirect_uri=REDIRECT_URI,
        code_verifier=code_verifier
    )

    flow.fetch_token(code=code)

    credentials = flow.credentials

    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not credentials.refresh_token and TOKEN_PATH.exists():
        with open(TOKEN_PATH, "r", encoding="utf-8") as file:
            old_credentials = json.load(file)
        credentials.refresh_token = old_credentials.get("refresh_token")

    with open(TOKEN_PATH, "w", encoding="utf-8") as file:
        file.write(credentials.to_json())

    session.pop("google_code_verifier", None)
    session.pop("google_oauth_state", None)

    return """
    <h2>Google Calendar connected successfully!</h2>
    <p>AutomationClinics is now connected to Google Calendar.</p>
    """
