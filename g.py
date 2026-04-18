import requests

url = "https://accounts.zoho.eu/oauth/v2/token"

data = {
    "grant_type": "authorization_code",
    "client_id": "1000.0U3TECJRGNP5ZTR9U0AH0AAF4EFJ1W",
    "client_secret": "8d950bd47174cf7ddce65b45d61b369185ccf87b7a",
    "redirect_uri": "http://localhost",
    "code": "1000.4b7989853a89339afe7c50259232c9e1.4e082900c3a17bcc9049c3db8709b325"
}

r = requests.post(url, data=data)
print(r.json())