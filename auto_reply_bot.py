import base64
import time
import sys
import logging
import threading
import os
from email.mime.text import MIMEText
from flask import Flask, jsonify, request
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import google.generativeai as genai

# === CONFIGURE LOGGING (so Render shows output) ===
logging.basicConfig(stream=sys.stdout, level=logging.INFO, force=True)
print = lambda *args, **kwargs: logging.info(" ".join(map(str, args)))

# === CONFIGURE GEMINI ===
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDEUcW7ml4iq88umeQRWGS_C0QCuyuBn30")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-pro")

def generate_ai_reply(email_text):
    prompt = f"""
    You are an intelligent email assistant. 
    Read the following email and generate a short, polite, helpful, and natural reply.
    If the email contains a question, try to answer it concisely.
    Keep the tone friendly and professional.

    EMAIL CONTENT:
    {email_text}

    Your reply:
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("⚠️ AI generation error:", e)
        return "Hello! Thanks for reaching out. We’ll get back to you soon."

# === GLOBAL STATUS ===
last_check_time = "Never"
last_action = "Idle"

# === MAIN EMAIL CHECK FUNCTION ===
def check_and_reply():
    global last_check_time, last_action
    try:
        creds = Credentials.from_authorized_user_file('token.json')
        service = build('gmail', 'v1', credentials=creds)

        print("🔍 Checking for unread emails...")
        last_action = "Checking inbox"
        results = service.users().messages().list(userId='me', q='is:unread').execute()
        messages = results.get('messages', [])
        print(f"📨 Found {len(messages)} unread email(s).")

        if not messages:
            print("📭 No new emails.")
            last_check_time = time.strftime("%Y-%m-%d %H:%M:%S")
            last_action = "No new emails"
            return

        for msg in messages:
            msg_id = msg['id']
            message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(no subject)')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            snippet = message.get('snippet', '')

            print(f"📩 New email from {sender} | Subject: {subject}")
            print("🧠 Generating AI reply...")

            ai_reply = generate_ai_reply(snippet)

            reply = MIMEText(ai_reply)
            reply['To'] = sender
            reply['Subject'] = f"Re: {subject}"

            raw_reply = base64.urlsafe_b64encode(reply.as_bytes()).decode()
            service.users().messages().send(userId="me", body={'raw': raw_reply}).execute()

            # Mark as read
            service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()

            print("✅ Smart AI reply sent!\n")

        last_check_time = time.strftime("%Y-%m-%d %H:%M:%S")
        last_action = "Replied to emails"

    except Exception as e:
        print("❌ Error in check_and_reply:", e)
        last_action = f"Error: {e}"

# === KEEP RENDER SERVICE ALIVE ===
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Email Auto-Reply Bot is running on Render!"

@app.route('/health')
def health():
    return "OK", 200

# === NEW ROUTE: Bot status for .exe ===
@app.route('/status')
def status():
    return jsonify({
        "status": "running",
        "last_check": last_check_time,
        "last_action": last_action
    })

# === NEW ROUTE: Recent emails for .exe ===
@app.route('/emails')
def get_emails():
    try:
        creds = Credentials.from_authorized_user_file('token.json')
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=5).execute()
        messages = results.get('messages', [])

        emails = []
        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='metadata',
                                                      metadataHeaders=['From', 'Subject', 'Date']).execute()
            headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
            emails.append({
                "from": headers.get('From', 'Unknown'),
                "subject": headers.get('Subject', '(No subject)'),
                "date": headers.get('Date', 'Unknown')
            })
        return jsonify(emails)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === NEW ROUTE: Manually trigger a check (from .exe button) ===
@app.route('/reply-now', methods=['POST'])
def reply_now():
    threading.Thread(target=check_and_reply).start()
    return jsonify({"status": "Triggered manual check"}), 200

# === RUN BOTH FLASK + EMAIL LOOP ===
if __name__ == "__main__":
    def run_flask():
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port)

    def run_email_bot():
        print("🤖 Smart auto-reply bot started! Checking inbox every 30 seconds...")
        while True:
            try:
                check_and_reply()
            except Exception as e:
                print("⚠️ Error in email loop:", e)
            time.sleep(30)

    threading.Thread(target=run_flask, daemon=True).start()
    run_email_bot()

