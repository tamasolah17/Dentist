
from google_calendar import get_available_slots, book_appointment

# 1. Check available slots
slots = get_available_slots("2026-11-05")

print("AVAILABLE SLOTS:")

for slot in slots:
    print(slot["start"], "->", slot["end"])

# 2. Book a test appointment
# Uncomment only when you want to create a real test event!

result = book_appointment(
    "2026-11-05T10:00:00+01:00",
    "Test Patient",
    "test@example.com"
)

print(result)
