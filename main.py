import os
from dotenv import load_dotenv
from notion_client import Client
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar"]

notion = Client(auth=os.getenv("NOTION_TOKEN"))

prev_incomplete_tasks = []


def main():
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
                        "date": {"on_or_after": datetime.today().isoformat()},
                    },
                    {
                        "property": "Captured!",
                        "checkbox": {"equals": True},
                    },
                ],
            },
        }
    )

    newly_added_tasks = list(set(all_incomplete_tasks) - set(prev_incomplete_tasks))


if __name__ == "__main__":
    main()
