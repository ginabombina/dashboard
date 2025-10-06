import io

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = "rare-mechanic-448617-n3-cac81343b243.json"
SPREADSHEET_ID = "1xwWo0-3QSJnBfZBwDazNxHg_HTqqeP3omKFG7lk64oc"
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