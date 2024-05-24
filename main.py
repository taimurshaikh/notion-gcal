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

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar"]

notion = Client(auth=os.getenv("NOTION_TOKEN"))

prev_incomplete_tasks = []


def get_new_tasks_from_notion():
    global prev_incomplete_tasks
    all_incomplete_tasks = notion.databases.query(
        **{
            "database_id": os.getenv("NOTION_DATABASE_ID"),
            "filter": {
                "and": [
                    {
                        "property": "Done",
                        "checkbox": {"equals": False},
                    },
                    {
                        "property": "Due Date",
                        "date": {"is_not_empty": True},
                    },
                    {
                        "property": "Due Date",
                        "date": {"on_or_after": datetime.datetime.today().isoformat()},
                    },
                    {
                        "property": "Captured!",
                        "checkbox": {"equals": True},
                    },
                ],
            },
        }
    )

    newly_added_tasks = all_incomplete_tasks["results"][len(prev_incomplete_tasks) :]

    prev_incomplete_tasks = all_incomplete_tasks["results"]

    return newly_added_tasks


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def add_tasks_to_gcal(events):
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        now = (
            datetime.datetime.now(datetime.UTC).isoformat() + "Z"
        )  # 'Z' indicates UTC time

        for e in events:
            print(e)
            event = {
                "summary": e["properties"]["Task Name"]["title"][0]["text"]["content"],
                "colorId": 6,
                "start": {
                    "date": e["properties"]["Due Date"]["date"]["start"],
                    "timeZone": "America/New_York",
                },
                "end": {
                    "date": e["properties"]["Due Date"]["date"]["start"],
                    "timeZone": "America/New_York",
                },
            }
            event = service.events().insert(calendarId="primary", body=event).execute()
            print("Event created: %s" % (event.get("htmlLink")))

    except HttpError as error:
        print(f"An error occurred: {error}")


def main():
    for i in range(10):
        new_tasks = get_new_tasks_from_notion()
        if new_tasks:
            add_tasks_to_gcal(new_tasks)
        time.sleep(10)


if __name__ == "__main__":
    main()
