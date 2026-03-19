import smtplib
import sqlite3
import csv
import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
import pandas as pd



from datetime import datetime

# =========================
# CONFIG
# =========================

DB_NAME = "dentist_outreach.db"

CSV_INPUT = "qualified_dentist_leads.csv"
CAMPAIGN_NAME = "Berlin_Dentists_Campaign"

SMTP_SERVER = "smtp-relay.brevo.com"
SMTP_PORT = 587
SMTP_USERNAME = "9bfe0b001@smtp-brevo.com"

SMTP_PASSWORD = "xsmtpsib-328c74420b4d6f2086fb4c0a37d2cba831b76a4d533c86b299b19b9994f5d2af-IUsjlFo35dQjJoXv"
SENDER_EMAIL = "thomas.meier@automationclinics.com"


SEND_DELAY = 3  # seconds between emails (anti-spam safety)
SENT_FILE = "sent_emails.txt"
print(SENT_FILE)
def load_sent_emails():
    if not os.path.exists(SENT_FILE):
        return set()
    with open(SENT_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_sent_email(email):
    with open(SENT_FILE, "a") as f:
        f.write(email + "\n")
import sqlite3



print("Statuses reset to pending.")
# =========================
# DATABASE SETUP
# =========================

def create_database():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS recipients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clinic_name TEXT,
            email TEXT UNIQUE,
            reviews INTEGER,
            city TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            campaign TEXT,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# =========================
# IMPORT QUALIFIED LEADS
# =========================


def import_leads():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    df = pd.read_csv(CSV_INPUT)

    for _, row in df.iterrows():

        if row["qualified"] != "YES":
            continue

        email = clean_email(row["email"])

        if not valid_email(email):
            continue

        clinic = row["name"]
        reviews = row["reviews"]
        city = "Berlin"

        try:
            c.execute("""
                INSERT OR IGNORE INTO recipients
                (clinic_name, email, reviews, city)
                VALUES (?, ?, ?, ?)
            """, (clinic, email, reviews, city))

        except:
            pass

    conn.commit()
    conn.close()

    print("Leads imported successfully.")


# =========================
# HELPER: Extract Doctor Last Name
# =========================

def extract_last_name(clinic_name):
    parts = clinic_name.split()
    for word in parts:
        if word.lower().startswith("dr"):
            return parts[-1]
    return "Doctor"


# =========================
# EMAIL TEMPLATE
# =========================

def generate_email(clinic_name, reviews, city):

    subject = f"Quick question about {clinic_name}"

    body_plain = f"""
Hi there,

I came across {clinic_name} while researching highly rated dental clinics in {city} — {reviews} Google reviews is impressive.

I noticed your website doesn’t currently offer an AI assistant for handling patient inquiries outside office hours.

Most clinics are using a lightweight AI reception system to capture those after-hours requests and convert them into booked appointments automatically.

I recorded a quick 60-second example: https://www.automationclinics.com/pages/ai-asisstant-demo
Worth taking a look?

Best regards,
Thomas Meier
Founder - AutomationClinics


If this isn’t relevant, just let me know and I won’t follow up.
"""

    body_html = f"""
<html>
<body>
<p>Hallo,</p>

<p>ich bin auf <strong>{clinic_name}</strong> gestoßen — <strong>{reviews} Bewertungen</strong> ist wirklich stark.</p>

<p><strong>Kurze Frage:</strong><br>
Werden bei Ihnen Anfragen außerhalb der Öffnungszeiten aktuell erfasst?</p>

<p>Viele Praxen verlieren genau dort täglich neue Patienten.</p>

<p>Ich habe dazu ein kurzes 60-Sekunden Beispiel vorbereitet:<br>
https://www.automationclinics.com/</p>

<p>Lohnt sich ein kurzer Blick?</p>

<p>mit Freundlichen Grüßen,<br>
Thomas Meier<br>
Founder - AutomationClinics<br>
</p>
<p style="text-align:left;margin-top:0px;">
<img src= "https://cdn.shopify.com/s/files/1/0930/3893/6393/files/AutoClinicsLogo17.jpg?v=1773769989" width="120" style="display:block;">
</p>
<p style="font-size:13px;color:gray;">
contact@automationclinics.com<br>
📍40212 Düsseldorf
Germany
</p>

</body>
</html>
"""

    return subject, body_plain, body_html


# =========================
# SEND EMAIL
# =========================

def send_email(to_address, subject, body_plain, body_html):
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_address
        msg["Subject"] = subject
        msg["Reply-To"] = SENDER_EMAIL

        msg.attach(MIMEText(body_plain, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_address, msg.as_string())

        return True

    except Exception as e:
        print(f"Error sending to {to_address}: {e}")
        return False


# =========================
# LOGGING
# =========================

def log_status(email, status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        INSERT INTO email_logs (email, campaign, status)
        VALUES (?, ?, ?)
    """, (email, CAMPAIGN_NAME, status))

    if status == "sent":
        c.execute("DELETE FROM recipients WHERE email = ?", (email,))
    else:
        c.execute("""
            UPDATE recipients
            SET status = ?
            WHERE email = ?
        """, (status, email))

    conn.commit()
    conn.close()


def clean_email(email):
    if email is None:
        return None

    email = str(email).strip()

    # remove html escape junk
    email = email.replace("u003e", "")
    email = email.replace(">", "")
    email = email.replace("<", "")

    return email
def valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email)
# =========================
# BULK SEND
# =========================

def send_bulk():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        SELECT clinic_name, email, reviews, city
        FROM recipients
        
    """)

    leads = c.fetchall()
    conn.close()

    if not leads:
        print("No pending leads.")
        return
    sent_emails = load_sent_emails()
    for clinic_name, email, reviews, city in leads:

        if email in sent_emails:
            print(f"Skipping already emailed: {email}")
            continue
        if not valid_email(email):
            print(f"Skipping invalid email: {email}")
            continue
        subject, body_plain, body_html = generate_email(clinic_name, reviews, city)

        success = send_email(email, subject, body_plain, body_html)

        log_status(email, "sent" if success else "failed")
        if success:
            save_sent_email(email)
        print(f"{clinic_name} → {'Sent' if success else 'Failed'}")

        time.sleep(SEND_DELAY)




# =========================
# RUN
# =========================

if __name__ == "__main__":
    create_database()
    import_leads()
    send_bulk()
