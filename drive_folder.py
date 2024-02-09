# drive_folder_creator.py

import os
import time
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class GoogleDriveFolderCreator:
    SCOPES = ['https://www.googleapis.com/auth/drive']
    TOKEN_PATH = 'token.json'
    FOLDER_ID = '1hCdGPyGdorhsBcPhg7lmtGiFFZXJMB1O'  # Update this with your specific folder ID

    def __init__(self):
        self.creds = self._authenticate()
        self.service = build('drive', 'v3', credentials=self.creds)

    def _authenticate(self):
        """Authenticate using the OAuth2 token."""
        creds = None
        if os.path.exists(self.TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(self.TOKEN_PATH, self.SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
        return creds

    def create_folder(self, folder_name, parent_folder_id=None):
        """Create a new folder on Google Drive."""
        if not parent_folder_id:
            parent_folder_id = self.FOLDER_ID
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_folder_id]
        }
        folder = self.service.files().create(
            body=file_metadata,
            fields='id',
            supportsAllDrives=True  # This is crucial for shared folders
        ).execute()
        return folder.get("id")

def create_folder_in_drive(parent_folder_id=None):
    """Function to create a folder in Google Drive with the current time in seconds as its name."""
    folder_name = str(int(time.time()))
    creator = GoogleDriveFolderCreator()
    folder_id = creator.create_folder(folder_name, parent_folder_id)
    print(f'New folder created with ID: {folder_id}')
    return folder_id
