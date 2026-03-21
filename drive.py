import io
import os
from dotenv import load_dotenv
load_dotenv()

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = os.getenv("SERVICE_ACCOUNT_FILE")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
OUTPUT_FILE = "sheet.csv"    

def download_file():
    """Authenticate with Google Drive and export the sheet as CSV."""

    try:
        # authorise with service-account details
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )


        # create drive api client
        service = build("drive", "v3", credentials=creds)

        # export as csv
        request = service.files().export_media(fileId=SPREADSHEET_ID, mimeType="text/csv")
        fh = io.FileIO(OUTPUT_FILE, "wb")
        fh.write(request.execute())
        fh.close()
        print("Download sucessful")

    except HttpError as error:
        print(f"An error occurred: {error}")
        return False

    return True


if __name__ == "__main__":
  download_file()