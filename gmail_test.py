from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

# Step 1: Gmail API scope (readonly for safety)
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def main():
    creds = None
    # Step 2: Check for saved token (auto-login after first time)
    if os.path.exists("token.json"):
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    else:
        # Step 3: Ask you to log in through Google the first time
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    # Step 4: Connect to Gmail
    service = build("gmail", "v1", credentials=creds)
    results = service.users().labels().list(userId="me").execute()
    labels = results.get("labels", [])

    print("\n✅ Gmail API connection successful!\n")
    print("Your Gmail labels:")
    for label in labels:
        print(f" - {label['name']}")

if __name__ == "__main__":
    main()
