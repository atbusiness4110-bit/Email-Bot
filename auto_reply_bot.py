from flask import Flask, request, jsonify
import os
import base64
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# In-memory log of sent emails
SENT_EMAILS = []

@app.route("/send-email", methods=["POST"])
def send_email():
    data = request.get_json()

    # Validate input
    if not data or not all(k in data for k in ("to", "subject", "body")):
        return jsonify({"error": "Missing fields"}), 400

    try:
        # Load Gmail credentials
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        service = build('gmail', 'v1', credentials=creds)

        # Build email
        message = EmailMessage()
        message.set_content(data["body"])
        message["To"] = data["to"]
        message["Subject"] = data["subject"]
        sender = os.getenv("EMAIL_ADDRESS") or "atbusiness4110@gmail.com"
        message["From"] = sender

        # Encode and send
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        send_message = service.users().messages().send(
            userId="me", body={"raw": encoded_message}
        ).execute()

        # Log the email
        email_entry = {
            "name": data.get("name", "Unknown"),
            "email": data["to"],
            "details": f"Subject: {data['subject']} | Body: {data['body'][:100]}...",
            "timestamp": datetime.utcnow().isoformat(),
        }
        SENT_EMAILS.append(email_entry)
        print(f"✅ Sent email logged: {email_entry}")

        return jsonify({"status": "success", "message_id": send_message["id"]}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/emails", methods=["GET"])
def get_emails():
    """Return all sent emails."""
    return jsonify(SENT_EMAILS), 200


@app.route("/summary", methods=["GET"])
def summary():
    """Return a simple summary of sent emails."""
    total = len(SENT_EMAILS)
    if total == 0:
        return "No emails sent yet."
    urgent = sum("urgent" in e["details"].lower() for e in SENT_EMAILS)
    latest = SENT_EMAILS[-1]["timestamp"]
    return f"{total} emails sent. {urgent} marked urgent. Last email at {latest}."


@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "message": "🤖 Email Bot is live and connected!",
        "emails_endpoint": "/emails",
        "summary_endpoint": "/summary"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
