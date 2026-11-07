"""Clinic registry: built-in test clinic plus database-backed client configurations."""

import json
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "instance" / "clinics.db"


# Initial test configuration.
# New clients are stored in SQLite via /admin/clinics.

CLINICS = {

    "clinic_001": {

        "name": "Shopify Test Clinic",

        "treatments": {

            "cleaning": {
                "names": {
                    "de": "Zahnreinigung",
                    "en": "Cleaning",
                    "hun": "Fogtisztítás"
                },
                "price": "89 €",
                "duration": 30
            },

            "whitening": {
                "names": {
                    "de": "Zahnaufhellung",
                    "en": "Whitening",
                    "hun": "Fogfehérítés"
                },
                "price": "349 €",
                "duration": 30
            },

            "implant": {
                "names": {
                    "de": "Implantat",
                    "en": "Implant",
                    "hun": "Implantátum"
                },
                "price": "1.790 €-tól",
                "duration": 30
            },

            "braces": {
                "names": {
                    "de": "Zahnspange",
                    "en": "Braces",
                    "hun": "Fogszabályozás"
                },
                "price": "2.490 €-tól",
                "duration": 30
            }

        },

        "opening_hours": {
            "start": "09:00",
            "end": "17:00",
            "weekdays": [0, 1, 2, 3, 4, 5, 6]
        },

        "calendar_id": "primary",

        "timezone": "Europe/Budapest",

        "slot_interval_minutes": 30

    }

}


def _connect():

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(DB_PATH)

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS clinics (
            clinic_id TEXT PRIMARY KEY,
            config_json TEXT NOT NULL
        )
        """
    )

    return connection


def get_clinic(clinic_id: str) -> dict:

    if clinic_id in CLINICS:
        return CLINICS[clinic_id]

    with _connect() as db:

        row = db.execute(
            "SELECT config_json FROM clinics WHERE clinic_id = ?",
            (clinic_id,)
        ).fetchone()

    if not row:
        raise ValueError(
            f"Unknown clinic_id: {clinic_id}"
        )

    return json.loads(row[0])


def clinic_exists(clinic_id: str) -> bool:

    try:
        get_clinic(clinic_id)
        return True

    except ValueError:
        return False


def save_clinic(clinic_id: str, config: dict) -> None:

    if not clinic_id or not clinic_id.replace(
        "_", ""
    ).replace("-", "").isalnum():

        raise ValueError(
            "clinic_id may contain only letters, numbers, underscores and hyphens"
        )

    if clinic_id in CLINICS:

        raise ValueError(
            "Built-in clinic IDs cannot be overwritten through the admin API"
        )

    required = (
        "name",
        "treatments",
        "opening_hours",
        "calendar_id",
        "timezone"
    )

    if any(key not in config for key in required):

        raise ValueError(
            "Config must include name, treatments, opening_hours, calendar_id and timezone"
        )

    with _connect() as db:

        db.execute(
            """
            INSERT INTO clinics (clinic_id, config_json)
            VALUES (?, ?)
            ON CONFLICT(clinic_id)
            DO UPDATE SET config_json=excluded.config_json
            """,
            (
                clinic_id,
                json.dumps(
                    config,
                    ensure_ascii=False
                )
            )
        )


def list_clinic_ids():

    with _connect() as db:

        rows = db.execute(
            "SELECT clinic_id FROM clinics ORDER BY clinic_id"
        ).fetchall()

    return sorted(
        set(CLINICS) | {
            row[0] for row in rows
        }
    )