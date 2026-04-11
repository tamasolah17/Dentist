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

CSV_INPUT = "enriched_dentists.csv"
CAMPAIGN_NAME = "Berlin_Dentists_Campaign"

SMTP_SERVER = "smtp-relay.brevo.com"
SMTP_PORT = 587
SMTP_USERNAME = "9bfe0b001@smtp-brevo.com"

SMTP_PASSWORD = "xsmtpsib-328c74420b4d6f2086fb4c0a37d2cba831b76a4d533c86b299b19b9994f5d2af-I8OX4eiG9ThICsN7"
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

        if int(row["reviews"]) < 35:
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

    subject = f"Kurze Frage zur {clinic_name}"

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
<html><html>
<body>

<p>Hallo,</p>

<p>ich habe mir <strong>{clinic_name}</strong> kurz angesehen — mit <strong>{reviews} Bewertungen</strong> gehören Sie definitiv zu den gefragteren Praxen in Ihrer Region.</p>

<p><strong>Kurze Frage:</strong></p>

<p>Was passiert bei Ihnen aktuell mit Anfragen, die abends oder am Wochenende reinkommen?</p>

<p>Viele Patienten kontaktieren mehrere Praxen gleichzeitig — und entscheiden sich meist für die, die zuerst reagiert.</p>

<p>Genau hier geht bei vielen Praxen ein Teil der Anfragen verloren, ohne dass es im Alltag auffällt — was sich langfristig auch auf die Konkurrenzfähigkeit gegenüber anderen 5-Sterne-Praxen auswirkt.</p>

<p>Wir haben eine Lösung, die solche Anfragen automatisch auffängt und priorisiert, sodass besonders relevante Anliegen direkt im Fokus stehen — ganz ohne zusätzlichen Aufwand.</p>

<p>Könnte das ggf. auch für den Praxisinhaber interessant sein?</p>


<p>Mit freundlichen Grüßen,<br>
Thomas Meier<br>
Founder - AutomationClinics</p>

<p style="margin-top:0; position: relative;">
  <img src="https://cdn.shopify.com/s/files/1/0930/3893/6393/files/ChatGPT_Image_2026._marc._8._03_47_26_1.png?v=1774406176"
       width="120"
       style="position: relative; left: 25px;">
</p>

<p style="font-size:13px;color:gray;">
thomas.meier@automationclinics.com<br>
📍40212 Düsseldorf<br>
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
    counter = 0
    for clinic_name, email, reviews, city in leads:

        if counter == 500 :
            break
        if email in sent_emails:
            print(f"Skipping already emailed: {email}")
            continue
        if not valid_email(email):
            print(f"Skipping invalid email: {email}")
            continue
        subject, body_plain, body_html = generate_email(clinic_name, reviews, city)

        success = send_email(email, subject, body_plain, body_html)

        log_status(email, "sent" if success else "failed")
        counter += 1
        if success:
            save_sent_email(email)
        print(f"{clinic_name} → {'Sent' if success else 'Failed'}")
        print("counter:", counter)
        time.sleep(SEND_DELAY)




# =========================
# RUN
# =========================

if __name__ == "__main__":
    create_database()
    import_leads()
    send_bulk()
