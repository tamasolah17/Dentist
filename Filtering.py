import requests
import pandas as pd
import re
# === CONFIG ===
CLIENT_ID = "1000.0U3TECJRGNP5ZTR9U0AH0AAF4EFJ1W"
CLIENT_SECRET = "8d950bd47174cf7ddce65b45d61b369185ccf87b7a"
REFRESH_TOKEN = "1000.09bf393b120f374af59dd07748239e84.02c24057ee6c4559b604a920f4da7994"

ACCOUNT_ID = "8588005000000002002"
CSV_FILE = "enriched_dentists.csv"

BAD_KEYWORDS = [
    "entfernen",
    "kein interesse",
    "kein Interesse",
    "nicht interessiert",
    "kein bedarf",
    "abmelden",
    "keine weiteren anfragen",
    "keine werbung",
    "senden sie uns keine werbung",
    "löschen sie unsere daten",
    "Ich möchte nichts mehr dazu bekommen." 
    "datenschutz",
    "behörde für datenschutz",
    "beschwerde",
    "unsubscribe",
    "lassen Sie mich",
    "nicht bekommen",
    "nicht mehr",
    "zu entfernen",
    "stop",
    "remove me"
    "entfernen",
    "kein interesse",
    "nicht interessiert",
    "kein bedarf",
    "abmelden",
    "keine weiteren anfragen",
    "keine werbung",
    "senden sie uns keine werbung",
    "löschen sie unsere daten",
    "ich möchte nichts mehr dazu bekommen",
    "datenschutz",
    "behörde für datenschutz",
    "beschwerde",
    "unsubscribe",
    "lassen sie mich",
    "nicht bekommen",
    "nicht mehr",
    "zu entfernen",
    "stop",
    "remove me",
    "zu unterlassen"
]


def normalize_email(email):
    if not email:
        return ""
    match = re.search(r'[\w\.-]+@[\w\.-]+', email)
    return match.group(0).lower() if match else email.lower()

# === STEP 1: GET ACCESS TOKEN ===
def get_access_token():
    url = "https://accounts.zoho.eu/oauth/v2/token"

    data = {
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token"
    }

    response = requests.post(url, data=data)
    return response.json()["access_token"]


# === STEP 2: GET INBOX FOLDER ID ===
def get_inbox_folder(access_token):
    url = f"https://mail.zoho.eu/api/accounts/{ACCOUNT_ID}/folders"

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }

    response = requests.get(url, headers=headers)

    print("RAW RESPONSE:", response.text[:500])

    try:
        data = response.json()
    except:
        print("❌ Not JSON response")
        return None

    # Handle weird Zoho list response
    if isinstance(data, list):
        data = data[1] if len(data) > 1 else data[0]

    if "data" not in data:
        print("❌ No folder data:", data)
        return None

    for folder in data["data"]:
        if isinstance(folder, dict):
            if folder.get("folderName", "").lower() == "inbox":
                return folder.get("folderId")

    print("❌ Inbox not found in:", data)
    return None


# === STEP 3: GET MESSAGES ===
def get_messages(access_token, folder_id):
    url = f"https://mail.zoho.eu/api/accounts/{ACCOUNT_ID}/messages/view"

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }

    params = {
        "folderId": folder_id,
        "limit": 500
    }

    response = requests.get(url, headers=headers, params=params)

    print("STATUS:", response.status_code)
    print("RAW:", response.text[:300])

    try:
        data = response.json()
    except:
        return {}

    # 🔥 Zoho sometimes returns list instead of dict
    if isinstance(data, list):
        data = data[1]

    return data

# === STEP 4: EXTRACT BAD SENDERS ===
def extract_bad_senders(data):
    bad_senders = set()

    if "data" not in data:
        return bad_senders

    for msg in data["data"]:
        content = (
            msg.get("subject", "") + " " +
            msg.get("summary", "")
        ).lower()

        sender = normalize_email(msg.get("fromAddress"))

        if sender and any(k in content for k in BAD_KEYWORDS):
            print(f"❌ BAD: {sender} → {content[:80]}")
            bad_senders.add(sender)

    return bad_senders


# === STEP 5: CLEAN CSV ===
def clean_csv(bad_senders):
    df = pd.read_csv(CSV_FILE)

    before = len(df)

    df_cleaned = df[~df["email"].isin(bad_senders)]

    after = len(df_cleaned)

    df_cleaned.to_csv(CSV_FILE, index=False)

    print(f"\nRemoved: {before - after}")
    print(f"Remaining: {after}")


# === RUN ===
if __name__ == "__main__":
    access_token = get_access_token()

    folder_id = get_inbox_folder(access_token)

    if not folder_id:
        print("❌ Inbox not found")
        exit()

    data = get_messages(access_token, folder_id)

    bad_senders = extract_bad_senders(data)

    clean_csv(bad_senders)

def test_accounts(access_token):
    url = "https://mail.zoho.eu/api/accounts"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    r = requests.get(url, headers=headers)
    print(r.status_code)
    print(r.text)

# after getting token
test_accounts(access_token)