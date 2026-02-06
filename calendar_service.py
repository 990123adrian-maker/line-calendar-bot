import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def add_event(event_data):
    token_info = json.loads(os.environ.get("GOOGLE_TOKEN"))
    creds = Credentials.from_authorized_user_info(token_info)

    service = build("calendar", "v3", credentials=creds

    event = {
        "summary": event_data["title"],
        "start": {"dateTime": event_data["start"].isoformat(), "timeZone": "Asia/Taipei"},
        "end": {"dateTime": event_data["end"].isoformat(), "timeZone": "Asia/Taipei"},
    }


    service.events().insert(calendarId="primary", body=event).execute()
