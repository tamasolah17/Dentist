import requests
import re
import csv

input_file = "high_value_dentists.csv"
output_file = "qualified_dentist_leads.csv"

chatbot_keywords = [
    "tawk", "intercom", "drift", "zendesk",
    "livechat", "crisp", "chatbase",
    "messenger", "chat-widget", "chatbot"
]

email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

results = []

with open(input_file, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        website = row.get("website")
        reviews = int(row.get("reviews", 0))

        row["email"] = ""
        row["chatbot_detected"] = "Unknown"
        row["qualified"] = "No"

        if not website:
            results.append(row)
            continue

        try:
            response = requests.get(website, timeout=6)
            html = response.text.lower()

            # Detect chatbot
            chatbot_found = any(keyword in html for keyword in chatbot_keywords)
            row["chatbot_detected"] = "Yes" if chatbot_found else "No"

            # Extract email
            emails = re.findall(email_pattern, html)
            if emails:
                row["email"] = emails[0]

            # Qualification logic
            if (
                reviews >= 80 and
                row["email"] != "" and
                row["chatbot_detected"] == "No"
            ):
                row["qualified"] = "YES"

            print(f"{row['name']} → Qualified: {row['qualified']}")

        except:
            row["chatbot_detected"] = "Error"

        results.append(row)

if results:
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print("Done. Master lead file created.")