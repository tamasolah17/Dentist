import requests
import re
import csv
from bs4 import BeautifulSoup

input_file = "high_value_dentists.csv"
output_file = "dentists_with_emails.csv"

email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

dentists_with_email = []

with open(input_file, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        website = row.get("website")

        if not website:
            continue

        try:
            response = requests.get(website, timeout=5)
            emails = re.findall(email_pattern, response.text)

            if emails:
                row["email"] = emails[0]
                dentists_with_email.append(row)
                print("Found email:", emails[0])

        except Exception as e:
            print("Error visiting:", website)

with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=dentists_with_email[0].keys())
    writer.writeheader()
    writer.writerows(dentists_with_email)

print("Done. Emails extracted.")