import requests
import csv
import time
import math
import os

# =========================================================
# CONFIG
# =========================================================

API_KEY = "AIzaSyDvrx5ua7YL8YfjNEA0JgCcjrxHge3Bi2g"

NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

OUTPUT_FILE = "swiss_austria_dentists.csv"

PROGRESS_FILE = "progress_dentist.txt"
IDS_FILE = "scraped_ids.txt"

SEARCH_TERMS = [
    "dentist",
    "zahnarzt",
    "dental clinic",
    "kieferorthopäde",
    "implantologie",
    "ästhetische zahnmedizin",
    "invisalign",
    "oral surgery",
    "dentista",
    "studio dentistico",
    "cabinet dentaire"
]

MIN_REVIEWS = 5

# Switzerland bounds
SWISS_BOUNDS = {
    "lat_min": 45.81,
    "lat_max": 47.81,
    "lng_min": 5.95,
    "lng_max": 10.49
}

# Austria bounds
AUSTRIA_BOUNDS = {
    "lat_min": 46.37,
    "lat_max": 49.02,
    "lng_min": 9.53,
    "lng_max": 17.16
}

GRID_SPACING_KM = 8
RADIUS = 6000

# =========================================================
# HELPERS
# =========================================================

def km_to_lat(km):
    return km / 111


def km_to_lng(km, lat):
    return km / (111 * math.cos(math.radians(lat)))


def generate_grid(bounds):

    points = []

    lat = bounds["lat_min"]

    while lat <= bounds["lat_max"]:

        lng_step = km_to_lng(GRID_SPACING_KM, lat)

        lng = bounds["lng_min"]

        while lng <= bounds["lng_max"]:

            points.append((
                round(lat, 6),
                round(lng, 6)
            ))

            lng += lng_step

        lat += km_to_lat(GRID_SPACING_KM)

    return points

# =========================================================
# PROGRESS SYSTEM
# =========================================================

def save_progress(
    search_index,
    total_searches,
    keyword,
    lat,
    lng,
    total_ids
):

    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:

        f.write(f"LAST_INDEX={search_index}\n")
        f.write(f"TOTAL_SEARCHES={total_searches}\n")
        f.write(f"KEYWORD={keyword}\n")
        f.write(f"LAT={lat}\n")
        f.write(f"LNG={lng}\n")
        f.write(f"TOTAL_IDS={total_ids}\n")
        f.write(f"TIME={time.strftime('%Y-%m-%d %H:%M:%S')}\n")


def save_place_id(place_id):

    with open(IDS_FILE, "a", encoding="utf-8") as f:
        f.write(place_id + "\n")


def load_scraped_ids():

    scraped_ids = set()

    if os.path.exists(IDS_FILE):

        with open(IDS_FILE, "r", encoding="utf-8") as f:

            for line in f:
                scraped_ids.add(line.strip())

    return scraped_ids


def load_progress():

    if not os.path.exists(PROGRESS_FILE):
        return 0

    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:

        lines = f.readlines()

    for line in lines:

        if line.startswith("LAST_INDEX="):
            return int(line.split("=")[1].strip())

    return 0

# =========================================================
# API CALLS
# =========================================================

def nearby_search(lat, lng, keyword):

    all_results = []
    next_page_token = None

    while True:

        params = {
            "location": f"{lat},{lng}",
            "radius": RADIUS,
            "keyword": keyword,
            "key": API_KEY
        }

        if next_page_token:

            params["pagetoken"] = next_page_token

            # Google requires delay before next page
            time.sleep(2)

        try:

            r = requests.get(NEARBY_URL, params=params, timeout=30)

            data = r.json()

            status = data.get("status")

            print("API STATUS:", status)

            if status not in ["OK", "ZERO_RESULTS"]:

                print("API ERROR:", data)

                break

            results = data.get("results", [])

            print("RESULT COUNT:", len(results))

            all_results.extend(results)

            next_page_token = data.get("next_page_token")

            if not next_page_token:
                break

        except Exception as e:

            print("SEARCH ERROR:", e)
            break

    return all_results


def get_details(place_id):

    params = {
        "place_id": place_id,
        "fields": ",".join([
            "name",
            "website",
            "formatted_phone_number",
            "formatted_address",
            "rating",
            "user_ratings_total",
            "types"
        ]),
        "key": API_KEY
    }

    try:

        r = requests.get(
            DETAILS_URL,
            params=params,
            timeout=30
        )

        data = r.json()

        if data.get("status") != "OK":

            print("DETAILS ERROR:", data)
            return None

        return data.get("result")

    except Exception as e:

        print("DETAIL REQUEST ERROR:", e)
        return None

# =========================================================
# LOAD EXISTING DATA
# =========================================================

existing_place_ids = set()

if os.path.exists(OUTPUT_FILE):

    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:

        reader = csv.DictReader(f)

        for row in reader:

            existing_place_ids.add(
                row["place_id"]
            )

# =========================================================
# MAIN
# =========================================================

all_places = {}

# LOAD EXISTING IDS
saved_ids = load_scraped_ids()

for pid in saved_ids:

    all_places[pid] = {
        "place_id": pid
    }

# CREATE GRID
grid_points = []

grid_points.extend(
    generate_grid(SWISS_BOUNDS)
)

grid_points.extend(
    generate_grid(AUSTRIA_BOUNDS)
)

print("TOTAL GRID POINTS:", len(grid_points))

# CREATE SEARCH JOBS
search_jobs = []

for lat, lng in grid_points:

    for term in SEARCH_TERMS:

        search_jobs.append((
            lat,
            lng,
            term
        ))

print("TOTAL SEARCHES:", len(search_jobs))

# LOAD LAST PROGRESS
start_index = load_progress()

print("RESUMING FROM SEARCH:", start_index)
print("ALREADY FOUND IDS:", len(all_places))

# =========================================================
# SEARCH PHASE
# =========================================================

for i in range(start_index, len(search_jobs)):

    lat, lng, term = search_jobs[i]

    print(
        f"[{i+1}/{len(search_jobs)}] "
        f"{term} @ {lat},{lng}"
    )

    try:

        results = nearby_search(
            lat,
            lng,
            term
        )

        for place in results:

            place_id = place.get("place_id")

            if not place_id:
                continue

            if place_id not in all_places:

                all_places[place_id] = {
                    "place_id": place_id,
                    "name": place.get("name"),
                    "lat": place["geometry"]["location"]["lat"],
                    "lng": place["geometry"]["location"]["lng"]
                }

                # SAVE ID IMMEDIATELY
                save_place_id(place_id)

        # SAVE PROGRESS
        save_progress(
            i + 1,
            len(search_jobs),
            term,
            lat,
            lng,
            len(all_places)
        )

    except Exception as e:

        print("SEARCH LOOP ERROR:", e)

    time.sleep(0.2)

print("UNIQUE PLACES FOUND:", len(all_places))

# =========================================================
# DETAILS PHASE
# =========================================================

file_exists = os.path.exists(OUTPUT_FILE)

with open(
    OUTPUT_FILE,
    "a",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "name",
            "address",
            "phone",
            "website",
            "rating",
            "reviews",
            "place_id"
        ]
    )

    if not file_exists:
        writer.writeheader()

    for idx, place_id in enumerate(all_places.keys()):

        # SKIP ALREADY SAVED
        if place_id in existing_place_ids:
            continue

        print(
            f"DETAILS "
            f"{idx+1}/{len(all_places)}"
        )

        try:

            details = get_details(place_id)

            if not details:
                continue

            reviews = details.get(
                "user_ratings_total",
                0
            )

            if reviews < MIN_REVIEWS:
                continue

            row = {
                "name": details.get("name"),
                "address": details.get("formatted_address"),
                "phone": details.get("formatted_phone_number"),
                "website": details.get("website"),
                "rating": details.get("rating"),
                "reviews": reviews,
                "place_id": place_id
            }

            writer.writerow(row)

            # SAVE TO DISK IMMEDIATELY
            f.flush()

            existing_place_ids.add(place_id)

        except Exception as e:

            print("DETAIL ERROR:", e)

        time.sleep(0.1)

print("DONE")