import smtplib
import sqlite3
import csv
import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import re
import pandas as pd
from email.header import Header
import smtplib
import socket
import requests

print(socket.getaddrinfo("smtp-relay.brevo.com", 587))
print(requests.get("https://api.ipify.org").text)



s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
print("OUTGOING IP:", s.getsockname()[0])
s.close()

from datetime import datetime

# =========================
# CONFIG
# =========================

DB_NAME = "dentist_outreach.db"

CSV_INPUT = "enriched_dentists.csv"
CAMPAIGN_NAME = "Berlin_Dentists_Campaign"

SMTP_SERVER = "smtp-relay.brevo.com"
SMTP_PORT = 587





SMTP_USERNAME = ["a937f5001@smtp-brevo.com","aa13fb001@smtp-brevo.com",
"a994af001@smtp-brevo.com"]




SMTP_PASSWORD = ["xsmtpsib-c2b7edbd2dcdc1e0d8c281f84cd961b29c6fa4042f8ecc4c272072a4985bbbe2-MbZtCZHRtfxwFFy5",
                 "xsmtpsib-6f20d26c56c3953808069a4747ecb8eca63509a435a58185cfce89e430b73bfd-vtQOiCZgTNaUFPxL","xsmtpsib-7d93eb08d571249d4718c253eb818cd92b0d36ca4d7523bc4b9c2b06b507469b-SjnAtxHJ9q7v5saT"]
SENDER_EMAIL = ["lukas.micheal@automationclinics.com", "thomas.meier@automationclinics.com","lukas.micheal@automationclinics.com"]



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
<html>
<body>

<p>Hallo,</p>

<p>ich bin Lukas Micheal, Gründer von AutomationClinics.</p>

<p>Viele Zahnarztpraxen verlieren potenzielle Patienten, obwohl diese bereits die Website besuchen. Besonders abends und am Wochenende entstehen Fragen zu Kosten, Behandlungen oder freien Terminen – und wenn niemand sofort antwortet, verlassen viele Interessenten die Seite wieder.</p>

<p>Dafür haben wir einen <strong>mehrsprachigen KI-Assistenten</strong> entwickelt, der direkt auf der Praxis-Website arbeitet.</p>

<p>Er beantwortet Patientenfragen in <strong>Deutsch, Englisch und einer weiteren Sprache</strong> rund um die Uhr, führt Besucher durch ein natürliches Gespräch und begleitet interessierte Patienten bis zur Terminanfrage. Dadurch wird die Rezeption von wiederkehrenden Fragen entlastet und aus bestehenden Website-Besuchern können mehr qualifizierte Anfragen entstehen.</p>

<p>Die Integration ist unkompliziert: Ein kurzer Code-Snippet genügt, und der Assistent kann <strong>innerhalb weniger Minuten</strong> auf der bestehenden Website eingebunden werden – ohne die bisherigen Praxisabläufe zu verändern.</p>

<p>Eine kurze Demo finden Sie hier:</p>

<p>
<a href="https://www.automationclinics.com/" target="_blank">
https://www.automationclinics.com/
</a>
</p>

<p>Falls das Thema für Ihre Praxis grundsätzlich interessant ist, zeige ich Ihnen gerne in einem kurzen <strong>10-minütigen Gespräch</strong>, wie der Assistent konkret auf Ihrer Website aussehen könnte.</p>

<p>Wäre ein kurzer Austausch nächste Woche für Sie interessant?</p>

<p>
Mit freundlichen Grüßen,<br><br>
<strong>Lukas Micheal</strong><br>
Gründer, AutomationClinics
</p>

<p style="font-size:13px;color:gray;">
lukas.micheal@automationclinics.com<br>
https://www.automationclinics.com/<br>
40212 Düsseldorf<br>
Germany
</p>

</body>
</html>
"""

    return subject, body_plain, body_html


# =========================
# SEND EMAIL
# =========================

def send_email(to_address, subject, body_plain, body_html, account_index):
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = SENDER_EMAIL[account_index]
        msg["To"] = to_address
        msg["Subject"] = Header(subject, "utf-8")
        msg["Reply-To"] = SENDER_EMAIL[account_index]

        msg.attach(MIMEText(body_plain, "plain", "utf-8"))
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(
                SMTP_USERNAME[account_index],
                SMTP_PASSWORD[account_index]
            )
            server.sendmail(
                SENDER_EMAIL[account_index],
                to_address,
                msg.as_string()
            )

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
    sent_count = len(sent_emails)
    for clinic_name, email, reviews, city in leads:


        if email in sent_emails:
            print(f"Skipping already emailed: {email}")
            continue
        if not valid_email(email):
            print(f"Skipping invalid email: {email}")
            continue
        subject, body_plain, body_html = generate_email(clinic_name, reviews, city)
        account_index = (sent_count // 300) % len(SMTP_USERNAME)

        print(f"Using account #{account_index + 1}: {SENDER_EMAIL[account_index]}")
        success = send_email(
            email,
            subject,
            body_plain,
            body_html,
            account_index
        )

        log_status(email, "sent" if success else "failed")
        if success:
            sent_count += 1


        print(f"{clinic_name} → {'Sent' if success else 'Failed'}")





        time.sleep(SEND_DELAY)




# =========================
# RUN
# =========================

if __name__ == "__main__":
    create_database()
    import_leads()
    send_bulk()
