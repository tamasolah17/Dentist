import requests
import csv
import time



germany_cities = [
   # Major cities
   "Berlin","Hamburg","Munich","Cologne","Frankfurt","Stuttgart",
   "Düsseldorf","Dortmund","Essen","Leipzig","Bremen","Dresden",

   # Secondary strong cities
   "Hanover","Nuremberg","Duisburg","Bochum","Wuppertal","Bielefeld",
#   "Bonn","Münster","Karlsruhe","Mannheim","Augsburg","Wiesbaden",

    # High-income / important regions
   "Heidelberg","Freiburg im Breisgau","Regensburg","Ulm","Würzburg",
   "Potsdam","Mainz","Kassel","Erfurt","Saarbrücken",

#    Munich region (VERY important)
    "Garching","Freising","Dachau","Erding","Starnberg","Fürstenfeldbruck"

    # Frankfurt region
#   "Offenbach","Darmstadt","Wiesbaden","Bad Homburg","Hanau",

    # Stuttgart region
#   "Esslingen","Ludwigsburg","Böblingen","Sindelfingen",

    # Hamburg region
#   "Altona","Norderstedt","Ahrensburg",

    # Berlin region
#   "Potsdam","Oranienburg","Bernau"
]

# austria_cities = [
    # Major cities
    # "Vienna","Graz","Linz","Salzburg","Innsbruck",

    # Secondary cities
    # "Klagenfurt","Villach","Wels","Sankt Pölten","Dornbirn",

    # Vienna region (VERY important)
    # "Mödling","Baden","Klosterneuburg","Schwechat","Korneuburg",

    # Graz region
    # "Seiersberg","Leibnitz","Voitsberg",

    # Linz region
    # "Steyr","Traun","Leonding",

    # Salzburg region
    # "Hallein","Seekirchen","Anif",

    # Innsbruck region
    # "Hall in Tirol","Telfs","Zirl"
# ]
switzerland_cities = [
    # Major cities
     "Zug","Lucerne","Winterthur","St. Gallen","Lugano",
     "Biel","Thun","Schaffhausen","Fribourg","Neuchatel",


    # Wealthy / high-income areas
     "Zurich","Geneva","Basel","Bern","Lausanne",


    # Zurich region (VERY IMPORTANT)
     "Kloten","Uster","Dübendorf","Wetzikon","Dietikon",

    # Geneva region
    "Carouge","Vernier","Nyon","Meyrin",

    # Basel region
    "Allschwil","Muttenz","Liestal",

    # Lausanne region
    "Montreux","Vevey","Yverdon-les-Bains"
]

BAD_KEYWORDS = [
    "dental21",
    "mvz",
    "zahnzentrum",
    "group",
    "clinic group",
    "chain",


    "dental group",
    "corporate"
]
HIGH_INTENT_QUERIES = [
    "Zahnarzt Implantologie",
    "Zahnarzt Notdienst",
    "Zahnarzt ästhetisch",
    "Kieferorthopäde",
    "Zahnarzt Invisalign",
    "Zahnarzt",
    "Dentist",
    "Zahnarzt Implantologie Zürich",
    "Ästhetische Zahnmedizin Zürich",
    "Invisalign Zürich",
    "Zahnarzt in",
    "Dentist in",
    "Zahnarzt Praxis",
    "Dental Praxis",
    "Zahnarzt Schweiz",
    "Dentist Switzerland"

]
SEARCH_QUERIES = []

#for city in germany_cities:
    #for query in HIGH_INTENT_QUERIES:
            #SEARCH_QUERIES.append(f"{query} {city}")
            #SEARCH_QUERIES.append(f"Zahnarzt {city}")
            ##SEARCH_QUERIES.append(f"Dentist {city}")
            #SEARCH_QUERIES.append(f"{query} near {city}")
            #SEARCH_QUERIES.append(f"{query} Umgebung {city}")

# for city in austria_cities:
    # SEARCH_QUERIES.append(f"Zahnarzt {city}")
    # SEARCH_QUERIES.append(f"Dentist {city}")


for city in switzerland_cities:
        SEARCH_QUERIES.append(f"Zahnarzt {city}")
        SEARCH_QUERIES.append(f"Dentist {city}")
for city in switzerland_cities:
    for query in HIGH_INTENT_QUERIES:
        SEARCH_QUERIES.append(f"{query} {city}")

SEARCH_QUERIES = list(set(SEARCH_QUERIES))

print("TOTAL QUERIES:", len(SEARCH_QUERIES))
print(SEARCH_QUERIES[:20])
MIN_REVIEWS = 20

API_KEY = "AIzaSyDpaKoegCAWmcHNgsXR_YEfFX3gSZAVrG0"
search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
details_url = "https://maps.googleapis.com/maps/api/place/details/json"
SENT_FILE = "sent_emails.txt"
SCRAPED_FILE = "scraped_places2.txt"

def load_scraped_places():
    try:
        with open(SCRAPED_FILE, "r") as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_scraped_place(place_id):
    with open(SCRAPED_FILE, "a") as f:
        f.write(place_id + "\n")

scraped_places = load_scraped_places()
def load_sent_emails():
    try:
        with open(SENT_FILE, "r") as f:
            return set(line.strip().lower() for line in f)
    except FileNotFoundError:
        return set()

def domain_from_email(email):
    return email.split("@")[-1]

sent_emails = load_sent_emails()
sent_domains = {domain_from_email(email) for email in sent_emails}
dentists = []
next_page_token = None
print("lol",SEARCH_QUERIES)
for SEARCH_QUERY in SEARCH_QUERIES:

    print(f"Searching: {SEARCH_QUERY}")

    next_page_token = None

    while True:
        params = {
            "query": SEARCH_QUERY,
            "key": API_KEY
        }

        if next_page_token:
            params["pagetoken"] = next_page_token
            time.sleep(2.5)  # Required by Google before using next_page_token

        response = requests.get(search_url, params=params)
        data = response.json()
        print(data)

        for place in data.get("results", []):

            place_id = place["place_id"]

            if place_id in scraped_places:
                continue

            name = place.get("name", "").lower()

            if any(bad in name for bad in BAD_KEYWORDS):
                continue



            scraped_places.add(place_id)


            details_params = {
                "place_id": place_id,
                "fields": "name,rating,user_ratings_total,website,formatted_phone_number,formatted_address",
                "key": API_KEY
            }
            details_response = requests.get(details_url, params=details_params)

            details_json = details_response.json()

            if details_json.get("status") != "OK":
                continue

            details = details_json.get("result", {})

            reviews = details.get("user_ratings_total", 0)
            website = details.get("website")

            print(details.get("name"), reviews)

            if reviews >= MIN_REVIEWS and website:
                dentists.append({
                    "name": details.get("name"),
                    "rating": details.get("rating"),
                    "reviews": reviews,
                    "website": website,
                    "phone": details.get("formatted_phone_number"),
                    "address": details.get("formatted_address"),
                    "place_id": place_id
                })

            time.sleep(0.5)

            save_scraped_place(place_id)

        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break


with open("scraped_places2.txt", "r") as f:
    unique_ids = sorted(set(line.strip() for line in f))

with open("scraped_places2.txt", "w") as f:
    for pid in unique_ids:
        f.write(pid + "\n")
if dentists:
    with open("high_value_dentists.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=dentists[0].keys())
        writer.writeheader()
        writer.writerows(dentists)

    print(f"Done. Collected {len(dentists)} high-value dentists.")
else:
    print("No dentists matched your filter.")