import requests
import csv
import time

API_KEY = "AIzaSyAjNM_VkYaYOuSw4Octp3LzdKh8Z6-ej-k"
SEARCH_QUERY = "dentist in Berlin"
MIN_REVIEWS = 100

search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
details_url = "https://maps.googleapis.com/maps/api/place/details/json"

dentists = []
next_page_token = None

while True:
    params = {
        "query": SEARCH_QUERY,
        "key": API_KEY
    }

    if next_page_token:
        params["pagetoken"] = next_page_token
        time.sleep(2)  # Required by Google before using next_page_token

    response = requests.get(search_url, params=params)
    data = response.json()
    print(data)

    for place in data.get("results", []):
        place_id = place["place_id"]

        details_params = {
            "place_id": place_id,
            "fields": "name,rating,user_ratings_total,website,formatted_phone_number,formatted_address",
            "key": API_KEY
        }

        details_response = requests.get(details_url, params=details_params)
        details = details_response.json().get("result", {})
        print(details.get("name"), details.get("user_ratings_total"))
        reviews = details.get("user_ratings_total", 0)
        website = details.get("website")

        if reviews >= MIN_REVIEWS:
            dentists.append({
                "name": details.get("name"),
                "rating": details.get("rating"),
                "reviews": reviews,
                "website": website,
                "phone": details.get("formatted_phone_number"),
                "address": details.get("formatted_address")
            })

    next_page_token = data.get("next_page_token")
    if not next_page_token:
        break

if dentists:
    with open("high_value_dentists.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=dentists[0].keys())
        writer.writeheader()
        writer.writerows(dentists)

    print(f"Done. Collected {len(dentists)} high-value dentists.")
else:
    print("No dentists matched your filter.")