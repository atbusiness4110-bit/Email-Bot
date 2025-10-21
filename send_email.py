from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from email.mime.text import MIMEText
import base64
import os

def send_email(recipient, subject, message_text):
    # Load credentials from token.json
    creds = Credentials.from_authorized_user_file('token.json')
    service = build('gmail', 'v1', credentials=creds)

    # Create the email
    message = MIMEText(message_text)
    message['to'] = recipient
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    # Send it!
    send_message = service.users().messages().send(
        userId="me",
        body={'raw': raw_message}
    ).execute()

    print(f"✅ Email sent successfully! Message ID: {send_message['id']}")

if __name__ == "__main__":
    to = input("📧 Enter recipient email: ")
    subject = input("✉️  Enter subject: ")
    body = input("📝 Enter message: ")

    send_email(to, subject, body)
