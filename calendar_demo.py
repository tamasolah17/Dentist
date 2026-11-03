from datetime import date, datetime
from threading import Lock

# Demo naptár: a foglalások a Python folyamat memóriájában élnek.
_bookings = {}
_lock = Lock()

DEMO_SLOTS = [
    "09:00",
    "10:00",
    "11:00",
    "13:00",
    "14:00",
    "15:00",
    "16:00"
]


def get_available_slots(date_text):
    """
    date_text formátuma: YYYY-MM-DD
    Visszaadja az adott nap szabad időpontjait.
    """
    try:
        selected_date = date.fromisoformat(date_text)
    except (ValueError, TypeError):
        return None

    if selected_date < date.today():
        return []

    # Demo klinikánál hétvégén nincs rendelés.
    if selected_date.weekday() >= 5:
        return []

    with _lock:
        booked = _bookings.get(date_text, set())
        return [
            slot for slot in DEMO_SLOTS
            if slot not in booked
        ]


def book_slot(date_text, time_text, user_id, name, phone, treatment):
    """
    Lefoglal egy időpontot, ha az még szabad.
    """
    available_slots = get_available_slots(date_text)

    if available_slots is None or time_text not in available_slots:
        return False

    with _lock:
        booked = _bookings.setdefault(date_text, set())

        # Újra ellenőrizzük a foglalást, hogy ne legyen dupla foglalás.
        if time_text in booked:
            return False

        booked.add(time_text)

    print("DEMO BOOKING CREATED:", {
        "date": date_text,
        "time": time_text,
        "user_id": user_id,
        "name": name,
        "phone": phone,
        "treatment": treatment
    })

    return True