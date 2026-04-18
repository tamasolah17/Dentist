import requests

ACCESS_TOKEN = "1000.59f1620e1340626ebed0ba9162d579b0.7280dea1b34e392a784e69749121173f"

url = "https://mail.zoho.eu/api/accounts"

headers = {
    "Authorization": f"Zoho-oauthtoken {ACCESS_TOKEN}"
}

r = requests.get(url, headers=headers)

print(r.status_code)
print(r.text)