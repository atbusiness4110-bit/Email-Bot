from flask import Flask, request, jsonify
import os
import base64
import time
import requests
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
import email

# ===============================
# 🔹 LOAD CONFIGURATION
# ===============================
load_dotenv()
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

RENDER_SERVER = os.getenv("RENDER_SERVER") or "https://email-bot-free.onrender.com"
BOT_EMAIL = os.getenv("EMAIL_ADDRESS") or "atbusiness4110@gmail.com"

# ===============================
# 🔹 FLASK APP (for local testing)
# ===============================
app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({"status": "running", "message": "🤖 Email Bot local app is live!"})

# ===============================
# 🔹 SEND EMAIL THROUGH GMAIL API
# ===============================
def send_email(to, subject, body):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    service = build('gmail', 'v1', credentials=creds)

    msg = EmailMessage()
    msg.set_content(body)
    msg["To"] = to
    msg["From"] = BOT_EMAIL
    msg["Subject"] = subject

    encoded = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    sent = service.users().messages().send(userId="me", body={"raw": encoded}).execute()
    print(f"✅ Sent email to {to} (ID: {sent['id']})")

    # Log to render server
    try:
        requests.post(f"{RENDER_SERVER}/send-email", json={
            "to": to,
            "subject": subject,
            "body": body
        })
    except Exception as e:
        print(f"⚠️ Could not send log to server: {e}")

# ===============================
# 🔹 CHECK FOR NEW EMAILS
# ===============================
def check_for_new_messages():
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    service = build('gmail', 'v1', credentials=creds)

    results = service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD']).execute()
    messages = results.get('messages', [])

    if not messages:
        return None

    for msg in messages:
        msg_id = msg['id']
        m = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        headers = m['payload']['headers']

        sender = next((h['value'] for h in headers if h['name'] == 'From'), None)
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "(no subject)")

        # Extract body text
        parts = m['payload'].get('parts', [])
        body_text = ""
        if parts:
            for part in parts:
                if part['mimeType'] == 'text/plain':
                    body_text = base64.urlsafe_b64decode(part['body']['data']).decode()
        else:
            body_text = base64.urlsafe_b64decode(m['payload']['body']['data']).decode()

        # Mark as read
        service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()

        print(f"📨 New email from {sender} — Subject: {subject}")
        return sender, subject, body_text

    return None

# ===============================
# 🔹 AUTO-REPLY LOGIC LOOP
# ===============================
def auto_reply_loop():
    print("🤖 Email Auto-Responder started...")
    while True:
        try:
            new_mail = check_for_new_messages()
            if new_mail:
                sender, subject, body = new_mail

                reply_msg = (
                    f"Hello,\n\n"
                    f"Thank you for your message regarding '{subject}'. "
                    f"This is an automated response from the Email Bot.\n\n"
                    f"Original message:\n{body}\n\n"
                    f"Best regards,\nAI Email Bot"
                )

                send_email(sender, f"Re: {subject}", reply_msg)
            else:
                print("📭 No new messages. Checking again in 30s...")

            time.sleep(30)
        except Exception as e:
            print(f"⚠️ Error in loop: {e}")
            time.sleep(30)

# ===============================
# 🔹 MAIN RUN
# ===============================
if __name__ == "__main__":
    from threading import Thread

    # Run Flask app and auto-reply loop simultaneously
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))).start()
    auto_reply_loop()
