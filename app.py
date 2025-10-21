from flask import Flask, request, jsonify
import os
import base64
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Route to send email
@app.route("/send-email", methods=["POST"])
def send_email():
    data = request.get_json()

    # Check for required fields
    if not data or not all(k in data for k in ("to", "subject", "body")):
        return jsonify({"error": "Missing fields"}), 400

    try:
        # Load authorized Gmail credentials
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        service = build('gmail', 'v1', credentials=creds)

        # Build email
        message = EmailMessage()
        message.set_content(data["body"])
        message["To"] = data["to"]
        message["Subject"] = data["subject"]
        message["From"] = os.getenv("EMAIL_ADDRESS") or "atbusiness4110@gmail.com"

        # Encode the message for Gmail API
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        # Send message
        send_message = service.users().messages().send(userId="me", body={"raw": encoded_message}).execute()

        return jsonify({"status": "success", "message_id": send_message["id"]}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
