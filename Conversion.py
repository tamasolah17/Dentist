import requests
import time
import csv
import re
import os
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
API_KEY = "AIzaSyDpaKoegCAWmcHNgsXR_YEfFX3gSZAVrG0"


DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

INPUT_FILE = "scraped_places2.txt"
OUTPUT_FILE = "enriched_dentists.csv"
FAILED_FILE = "enriched_failed.csv"
PROGRESS_FILE = "progress.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

MAX_WORKERS = 1
REQUEST_DELAY = 0.5
MIN_REVIEWS = 10

write_lock = Lock()
progress_lock = Lock()

# -----------------------------
# PROGRESS
# -----------------------------
def load_progress():
    if not os.path.exists(PROGRESS_FILE):
        return 0
    try:
        with open(PROGRESS_FILE, "r") as f:
            content = f.read().strip()
            return int(content) if content else 0
    except:
        return 0

def save_progress(index):
    with progress_lock:
        try:
            with open(PROGRESS_FILE, "w") as f:
                f.write(str(index))
        except:
            pass

# -----------------------------
# FILE SETUP
# -----------------------------
def ensure_file(file, fields):
    exists = os.path.isfile(file)
    with open(file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            writer.writeheader()

# ✅ UPDATED HEADER (includes rating)
ensure_file(OUTPUT_FILE, ["name", "rating", "reviews", "email", "website"])
ensure_file(FAILED_FILE, ["place_id", "reason"])

def log_failed(place_id, reason):
    with write_lock:
        with open(FAILED_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["place_id", "reason"])
            writer.writerow({
                "place_id": place_id,
                "reason": reason
            })

# -----------------------------
# EXISTING DATA (DEDUP)
# -----------------------------
def normalize_website(url):
    if not url:
        return None
    return url.rstrip("/").lower()

def load_existing_entries():
    existing = set()

    if not os.path.isfile(OUTPUT_FILE):
        return existing

    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            website = normalize_website(row.get("website"))
            if website:
                existing.add(website)

    return existing

existing_websites = load_existing_entries()

# -----------------------------
# EMAIL EXTRACTION
# -----------------------------
def extract_emails_from_website(url):
    try:
        r = requests.get(url, timeout=6, headers=HEADERS)
        html = r.text.lower()

        emails = set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}", html))
        emails.update(re.findall(r"mailto:([^\"]+)", html))

        return list(emails)
    except:
        return []

def guess_email(domain):
    return f"info@{domain}"

def get_best_email(emails, website):
    if not emails:
        return None

    domain = urlparse(website).netloc

    for email in emails:
        if domain in email:
            return email

    return emails[0]

# -----------------------------
# PROCESS
# -----------------------------
def process_place(args):
    i, total, place_id = args

    try:
        print(f"\n[{i}/{total}] Processing {place_id}", flush=True)

        params = {
            "place_id": place_id,
            # ✅ INCLUDE RATING
            "fields": "name,rating,user_ratings_total,website",
            "key": API_KEY
        }

        res = requests.get(DETAILS_URL, params=params)
        json_data = res.json()

        status = json_data.get("status")
        error_message = json_data.get("error_message")

        print("API STATUS:", status, flush=True)

        if error_message:
            print("❌ ERROR MESSAGE:", error_message, flush=True)

        if status != "OK":
            reason = f"{status} | {error_message}" if error_message else status
            log_failed(place_id, reason)
            return

        data = json_data.get("result", {})

        name = data.get("name")
        # ✅ DEFAULT RATING = 4.5
        rating = round(float(data.get("rating", 4.5)), 1)
        reviews = data.get("user_ratings_total", 0)
        website = data.get("website")

        print(f"→ {name} | Rating: {rating} | Reviews: {reviews}", flush=True)

        if not name or reviews == 0:
            log_failed(place_id, "Empty result")
            return

        if reviews < MIN_REVIEWS:
            return

        if not website:
            log_failed(place_id, "No website")
            return

        website = normalize_website(website)

        # ✅ SKIP IF ALREADY EXISTS
        if website in existing_websites:
            print("⏭️ Skipping (already processed)", flush=True)
            return

        print("🌐 Scraping...", flush=True)

        emails = extract_emails_from_website(website)
        email = get_best_email(emails, website)

        if not email:
            domain = urlparse(website).netloc
            email = guess_email(domain)

        print(f"✅ {email}", flush=True)

        with write_lock:
            with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["name", "rating", "reviews", "email", "website"]
                )
                writer.writerow({
                    "name": name,
                    "rating": rating,
                    "reviews": reviews,
                    "email": email,
                    "website": website
                })

        # ✅ UPDATE MEMORY
        existing_websites.add(website)

        save_progress(i)

        time.sleep(REQUEST_DELAY)

    except Exception as e:
        print("ERROR:", e, flush=True)
        log_failed(place_id, str(e))

# -----------------------------
# MAIN
# -----------------------------
def load_place_ids():
    with open(INPUT_FILE, "r") as f:
        return [line.strip() for line in f]

if __name__ == "__main__":
    place_ids = load_place_ids()
    total = len(place_ids)

    start = load_progress()

    print(f"\n🚀 STARTING FROM {start}/{total}\n", flush=True)

    args_list = [
        (i+1, total, pid)
        for i, pid in enumerate(place_ids[start:], start=start)
    ]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(process_place, args_list)