"""Clinic-specific Google OAuth. Each clinic gets its own token file."""

import os
from pathlib import Path

from flask import (
    Blueprint,
    redirect,
    request,
    session,
    jsonify
)

from google_auth_oauthlib.flow import Flow

from clinics import (
    clinic_exists,
    get_clinic
)

from google_calendar import (
    token_path,
    SCOPES
)


google_auth = Blueprint(
    "google_auth",
    __name__
)


REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    "http://localhost:5000/google/callback"
)


def get_client_config():

    client_id = os.getenv("GOOGLE_CLIENT_ID")

    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:

        raise RuntimeError(
            "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET "
            "environment variables are required"
        )

    return {
        "web": {

            "client_id": client_id,

            "client_secret": client_secret,

            "auth_uri": (
                "https://accounts.google.com/o/oauth2/auth"
            ),

            "token_uri": (
                "https://oauth2.googleapis.com/token"
            ),

            "redirect_uris": [
                REDIRECT_URI
            ]

        }
    }


@google_auth.get("/google/login")
def google_login():

    clinic_id = request.args.get(
        "clinic_id",
        ""
    ).strip()

    if not clinic_exists(clinic_id):

        return jsonify({
            "error": "Valid clinic_id is required"
        }), 400

    try:

        flow = Flow.from_client_config(
            get_client_config(),
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )

        authorization_url, state = flow.authorization_url(

            access_type="offline",

            prompt="consent",

            include_granted_scopes="true",

            code_challenge_method="S256"

        )

        pending = session.get(
            "google_oauth_pending",
            {}
        )

        pending[state] = {

            "clinic_id": clinic_id,

            "code_verifier": flow.code_verifier

        }

        session["google_oauth_pending"] = pending

        session.modified = True

        return redirect(
            authorization_url
        )

    except Exception as exc:

        return jsonify({

            "error": "Could not start Google OAuth",

            "details": str(exc)

        }), 500


@google_auth.get("/google/callback")
def google_callback():

    state = request.args.get(
        "state",
        ""
    )

    pending = session.get(
        "google_oauth_pending",
        {}
    )

    oauth_data = pending.pop(
        state,
        None
    )

    session["google_oauth_pending"] = pending

    session.modified = True

    if not oauth_data:

        return jsonify({

            "error": (
                "Invalid or expired OAuth state. "
                "Restart /google/login?clinic_id=..."
            )

        }), 400

    if request.args.get("error"):

        return jsonify({

            "error": "Google authorization failed",

            "details": request.args.get("error")

        }), 400

    if not request.args.get("code"):

        return jsonify({

            "error": "Authorization code missing"

        }), 400

    clinic_id = oauth_data["clinic_id"]

    try:

        get_clinic(clinic_id)

        flow = Flow.from_client_config(

            get_client_config(),

            scopes=SCOPES,

            state=state,

            redirect_uri=REDIRECT_URI,

            code_verifier=oauth_data.get(
                "code_verifier"
            )

        )

        flow.fetch_token(
            code=request.args["code"]
        )

        credentials = flow.credentials

        path = token_path(clinic_id)

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # Google may omit refresh_token on subsequent
        # consent flows. Preserve the old one.

        if not credentials.refresh_token and path.exists():

            from google.oauth2.credentials import Credentials

            old = Credentials.from_authorized_user_file(
                str(path),
                scopes=SCOPES
            )

            credentials.refresh_token = old.refresh_token

        path.write_text(
            credentials.to_json(),
            encoding="utf-8"
        )

        return (
            f"<h2>Google Calendar connected successfully</h2>"
            f"<p>Clinic: {clinic_id}</p>"
        )

    except Exception as exc:

        return jsonify({

            "error": "Google Calendar connection failed",

            "details": str(exc)

        }), 500