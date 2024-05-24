import os
from dotenv import load_dotenv
from notion_client import Client
import datetime

import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

# Google Calendar API scopes
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Notion client object
notion = Client(auth=os.getenv("NOTION_TOKEN"))

# Global variable to track previously seen tasks
prev_incomplete_tasks = []


def get_new_tasks_from_notion():
    """
    Retrieves newly added incomplete tasks from Notion database.
    """
    global prev_incomplete_tasks
    # Construct filter criteria for incomplete tasks with upcoming due dates
    filter_criteria = {
        "and": [
            {"property": "Done", "checkbox": {"equals": False}},
            {"property": "Due Date", "date": {"is_not_empty": True}},
            {
                "property": "Due Date",
                "date": {"on_or_after": datetime.datetime.today().isoformat()},
            },
            {"property": "Captured!", "checkbox": {"equals": True}},
        ]
    }

    # Query Notion database for tasks meeting the criteria
    all_incomplete_tasks = notion.databases.query(
        database_id=os.getenv("NOTION_DATABASE_ID"), filter=filter_criteria
    )

    # Extract new tasks by comparing with previously seen tasks
    new_tasks = [
        task
        for task in all_incomplete_tasks["results"]
        if task not in prev_incomplete_tasks
    ]

    # Update global variable with current task list
    prev_incomplete_tasks = all_incomplete_tasks["results"]

    return new_tasks


def add_tasks_to_gcal(events):
    """
    Adds given events to Google Calendar.
    """
    # Initialize Google Calendar API credentials
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    # Build Google Calendar API service
    service = build("calendar", "v3", credentials=creds)

    # Process each event for insertion
    for event in events:
        event_details = {
            "summary": event["properties"]["Task Name"]["title"][0]["text"]["content"],
            "colorId": 6,
            "start": {
                "date": event["properties"]["Due Date"]["date"]["start"],
                "timeZone": "America/New_York",
            },
            "end": {
                "date": event["properties"]["Due Date"]["date"]["start"],
                "timeZone": "America/New_York",
            },
        }
        try:
            created_event = (
                service.events()
                .insert(calendarId="primary", body=event_details)
                .execute()
            )
            print(f"Event created: {created_event.get('htmlLink')}")
        except HttpError as error:
            print(f"Error creating event: {error}")


def main():
    """
    Continuously checks for new tasks and adds them to Google Calendar.
    """
    while True:
        new_tasks = get_new_tasks_from_notion()
        if new_tasks:
            add_tasks_to_gcal(new_tasks)
        time.sleep(10)


if __name__ == "__main__":
    main()
