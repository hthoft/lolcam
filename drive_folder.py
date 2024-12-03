import os
import time
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json

# Load configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)


class GoogleDriveFolderCreator:
    def __init__(self):
        self.scopes = config["google_drive"]["scopes"]
        self.token_path = config["google_drive"]["token_path"]
        self.default_folder_id = config["google_drive"]["default_folder_id"]
        self.credentials_file = config["google_drive"]["credentials_file"]
        self.creds = self._authenticate()
        self.service = build('drive', 'v3', credentials=self.creds)

    def _authenticate(self):
        """Authenticate using the OAuth2 token."""
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes)
                creds = flow.run_local_server(port=0)
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        return creds

    def create_folder(self, folder_name, parent_folder_id=None):
        """Create a new folder on Google Drive."""
        if not parent_folder_id:
            parent_folder_id = self.default_folder_id
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        folder = self.service.files().create(
            body=file_metadata,
            fields='id',
            supportsAllDrives=True
        ).execute()
        return folder.get("id")


def create_folder_in_drive(parent_folder_id=None):
    """Create a folder in Google Drive with the current time in seconds as its name."""
    folder_name = str(int(time.time()))
    creator = GoogleDriveFolderCreator()
    folder_id = creator.create_folder(folder_name, parent_folder_id)
    print(f'New folder created with ID: {folder_id}')
    return folder_id
