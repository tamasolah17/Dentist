import csv

input_file = "qualified_dentist_leads.csv"
output_file = "outreach_emails.txt"

template = """
Subject: Quick idea for {name}

Hi {name},

I noticed you have {reviews} Google reviews — impressive reputation.

While reviewing your website, I saw there’s currently no automated assistant handling patient inquiries outside office hours.

I build AI reception systems specifically for dental clinics that help convert website visitors into booked appointments automatically.

Would you be open to a short 10-minute demo customized for your clinic?

Best regards,
Your Name
"""

with open(input_file, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    emails = []

    for row in reader:
        if row.get("qualified") == "YES":
            email_text = template.format(
                name=row.get("name"),
                reviews=row.get("reviews")
            )
            emails.append(email_text)

with open(output_file, "w", encoding="utf-8") as f:
    for email in emails:
        f.write(email)
        f.write("\n" + "="*60 + "\n")

print("Email file generated.")