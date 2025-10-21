import base64
import time
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from email.mime.text import MIMEText
import google.generativeai as genai
from flask import Flask
import threading
import os

# === CONFIGURE GEMINI ===
GEMINI_API_KEY = "AIzaSyDEUcW7ml4iq88umeQRWGS_C0QCuyuBn30"
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

def check_and_reply():
    creds = Credentials.from_authorized_user_file('token.json')
    service = build('gmail', 'v1', credentials=creds)

    print("🔍 Checking for unread emails...")
    results = service.users().messages().list(userId='me', q='is:unread').execute()
    messages = results.get('messages', [])
    print(f"📨 Found {len(messages)} unread email(s).")

    if not messages:
        print("📭 No new emails.")
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

        # Mark email as read
        service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()

        print("✅ Smart AI reply sent!\n")

# === KEEP RENDER SERVICE ALIVE ===
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Email Auto-Reply Bot is running on Render!"

@app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Start Flask server in background thread
    threading.Thread(target=run_flask, daemon=True).start()

    print("🤖 Smart auto-reply bot started! Checking inbox every 30 seconds...")
    while True:
        check_and_reply()
        time.sleep(30)
