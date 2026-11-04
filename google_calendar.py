
import json
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

TOKEN_PATH = Path(__file__).parent / "instance" / "google_token.json"

TIMEZONE = ZoneInfo("Europe/Budapest")


def get_calendar_service():
    if not TOKEN_PATH.exists():
        raise RuntimeError("Google token file not found. Connect Google Calendar first.")

    credentials = Credentials.from_authorized_user_file(
        str(TOKEN_PATH),
        scopes=[
            "https://www.googleapis.com/auth/calendar.events.freebusy",
            "https://www.googleapis.com/auth/calendar.events.owned",
        ]
    )

    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

        TOKEN_PATH.write_text(
            credentials.to_json(),
            encoding="utf-8"
        )

    return build("calendar", "v3", credentials=credentials)


def get_available_slots(date, duration_minutes=30):
    """
    date format: YYYY-MM-DD
    Returns available appointment slots.
    """

    service = get_calendar_service()

    start_of_day = datetime.fromisoformat(date).replace(
        hour=9, minute=0, tzinfo=TIMEZONE
    )

    end_of_day = start_of_day.replace(hour=17, minute=0)

    events_result = service.events().list(
        calendarId="primary",
        timeMin=start_of_day.isoformat(),
        timeMax=end_of_day.isoformat(),
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = events_result.get("items", [])

    busy_periods = []

    for event in events:
        start = event["start"].get("dateTime")
        end = event["end"].get("dateTime")

        if start and end:
            busy_periods.append((
                datetime.fromisoformat(start),
                datetime.fromisoformat(end)
            ))

    available_slots = []
    current = start_of_day

    while current + timedelta(minutes=duration_minutes) <= end_of_day:

        slot_end = current + timedelta(minutes=duration_minutes)

        is_available = not any(
            current < busy_end and slot_end > busy_start
            for busy_start, busy_end in busy_periods
        )

        if is_available:
            available_slots.append({
                "start": current.isoformat(),
                "end": slot_end.isoformat()
            })

        current += timedelta(minutes=30)

    return available_slots



def book_appointment(
    start_time,
    patient_name,
    patient_email="",
    patient_phone="",
    treatment="Consultation"
):
    """
    Creates a 30-minute appointment only if the slot is available.
    """

    service = get_calendar_service()

    start = datetime.fromisoformat(start_time)

    if start.tzinfo is None:
        raise ValueError("start_time must include a timezone.")

    # Check availability again immediately before booking
    available_slots = get_available_slots(start.date().isoformat())

    slot_is_available = any(
        datetime.fromisoformat(slot["start"]) == start
        for slot in available_slots
    )

    if not slot_is_available:
        raise ValueError("This appointment slot is no longer available.")

    end = start + timedelta(minutes=30)

    event = {
        "summary": f"Dental appointment - {patient_name}",
        "description": (
            f"Patient: {patient_name}\n"
            f"Phone: {patient_phone}\n"
            f"Email: {patient_email}\n"
            f"Treatment: {treatment}"
        ),
        "start": {
            "dateTime": start.isoformat(),
            "timeZone": "Europe/Budapest"
        },
        "end": {
            "dateTime": end.isoformat(),
            "timeZone": "Europe/Budapest"
        }
    }

    created_event = service.events().insert(
        calendarId="primary",
        body=event
    ).execute()

    return {
        "status": "booked",
        "event_id": created_event["id"],
        "event_link": created_event.get("htmlLink")
    }
