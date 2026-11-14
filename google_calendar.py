"""Google Calendar operations isolated by clinic_id (one OAuth token per clinic)."""

from datetime import datetime, timedelta, time
from pathlib import Path
from zoneinfo import ZoneInfo
import os
import json

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from clinics import get_clinic


BASE_DIR = Path(__file__).resolve().parent

TOKEN_DIR = (
    BASE_DIR
    / "instance"
    / "google_tokens"
)



SCOPES = [
    "https://www.googleapis.com/auth/calendar.events"
]


def token_path(clinic_id: str) -> Path:

    # clinic_id is validated against configured clinics.
    get_clinic(clinic_id)

    return TOKEN_DIR / f"{clinic_id}.json"



def get_calendar_service(clinic_id: str):
    clinic = get_clinic(clinic_id)
    path = token_path(clinic_id)

    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(
            "GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET is missing."
        )

    if not path.exists():
        raise RuntimeError(
            f"Google Calendar is not connected for {clinic_id}. "
            f"Visit /google/login?clinic_id={clinic_id}"
        )

    with open(path, "r", encoding="utf-8") as f:
        token_info = json.load(f)

    # Mindig az aktuális .env OAuth-adatait használjuk.
    token_info["client_id"] = client_id
    token_info["client_secret"] = client_secret

    credentials = Credentials.from_authorized_user_info(
        token_info,
        scopes=SCOPES
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

        path.write_text(
            credentials.to_json(),
            encoding="utf-8"
        )

    if not credentials.valid:
        raise RuntimeError(
            f"Google credentials are invalid for {clinic_id}. "
            "Reconnect Google Calendar."
        )

    return build(
        "calendar",
        "v3",
        credentials=credentials,
        cache_discovery=False
    )



def _local_day_bounds(date_string: str, clinic: dict):

    tz = ZoneInfo(
        clinic.get(
            "timezone",
            "Europe/Budapest"
        )
    )

    day = datetime.strptime(
        date_string,
        "%Y-%m-%d"
    ).date()

    hours = clinic.get("opening_hours") or {}

    weekdays = hours.get(
        "weekdays",
        [0, 1, 2, 3, 4, 5, 6]
    )

    if day.weekday() not in weekdays:
        return None, None

    start_time = time.fromisoformat(
        hours.get("start", "09:00")
    )

    end_time = time.fromisoformat(
        hours.get("end", "17:00")
    )

    start = datetime.combine(
        day,
        start_time,
        tzinfo=tz
    )

    end = datetime.combine(
        day,
        end_time,
        tzinfo=tz
    )

    if end <= start:

        raise ValueError(
            "Clinic closing time must be later than opening time."
        )

    return start, end


def get_available_slots(
    date: str,
    clinic_id: str,
    duration_minutes: int = 30
):

    clinic = get_clinic(clinic_id)

    calendar_id = clinic.get("calendar_id")

    if not calendar_id:

        raise RuntimeError(
            f"No calendar_id configured for {clinic_id}."
        )

    start_day, end_day = _local_day_bounds(
        date,
        clinic
    )

    if start_day is None:
        return []

    service = get_calendar_service(clinic_id)

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=start_day.isoformat(),
        timeMax=end_day.isoformat(),
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    busy = []

    for event in events_result.get("items", []):

        event_start = event.get(
            "start",
            {}
        ).get("dateTime")

        event_end = event.get(
            "end",
            {}
        ).get("dateTime")

        # All-day events block the entire date.

        if (
            event.get("start", {}).get("date")
            or event.get("end", {}).get("date")
        ):

            return []

        if event_start and event_end:

            busy.append((
                datetime.fromisoformat(event_start),
                datetime.fromisoformat(event_end)
            ))

    interval = int(
        clinic.get(
            "slot_interval_minutes",
            30
        )
    )

    duration = timedelta(
        minutes=int(duration_minutes)
    )

    step = timedelta(
        minutes=interval
    )

    slots = []

    current = start_day

    while current + duration <= end_day:

        slot_end = current + duration

        is_available = not any(
            current < busy_end and slot_end > busy_start
            for busy_start, busy_end in busy
        )

        if is_available:

            slots.append({
                "start": current.isoformat(),
                "end": slot_end.isoformat()
            })

        current += step

    return slots


def book_appointment(
    start_time: str,
    patient_name: str,
    patient_phone: str = "",
    treatment: str = "Consultation",
    clinic_id: str = "clinic_001",
    patient_email: str = "",
    duration_minutes: int = 30
):

    clinic = get_clinic(clinic_id)

    calendar_id = clinic.get("calendar_id")

    if not calendar_id:

        raise RuntimeError(
            f"No calendar_id configured for {clinic_id}."
        )

    start = datetime.fromisoformat(start_time)

    if start.tzinfo is None:

        raise ValueError(
            "start_time must include a timezone."
        )

    # Re-check immediately before creating the event.

    slots = get_available_slots(
        start.date().isoformat(),
        clinic_id,
        duration_minutes
    )

    if not any(
        datetime.fromisoformat(slot["start"]) == start
        for slot in slots
    ):

        raise ValueError(
            "This appointment slot is no longer available."
        )

    end = start + timedelta(
        minutes=duration_minutes
    )

    timezone_name = clinic.get(
        "timezone",
        "Europe/Budapest"
    )

    event = {

        "summary": (
            f"Dental appointment - {patient_name}"
        ),

        "description": (
            f"Clinic: {clinic.get('name', clinic_id)}\n"
            f"Patient: {patient_name}\n"
            f"Phone: {patient_phone}\n"
            f"Email: {patient_email}\n"
            f"Treatment: {treatment}"
        ),

        "start": {
            "dateTime": start.isoformat(),
            "timeZone": timezone_name
        },

        "end": {
            "dateTime": end.isoformat(),
            "timeZone": timezone_name
        }

    }

    service = get_calendar_service(clinic_id)

    created = service.events().insert(
        calendarId=calendar_id,
        body=event
    ).execute()

    return {
        "status": "booked",
        "event_id": created["id"],
        "event_link": created.get("htmlLink")
    }