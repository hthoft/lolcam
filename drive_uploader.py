import os
import io
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Load configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)


class GoogleDriveUploader:
    def __init__(self):
        self.scopes = config["google_drive"]["scopes"]
        self.token_path = config["google_drive"]["token_path"]
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

    def upload_file(self, file_path, folder_id, file_name=None):
        """Upload a file to a specified folder on Google Drive."""
        if not file_name:
            file_name = os.path.basename(file_path)
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        # Assuming the uploaded file is an image; adjust the MIME type as needed.
        media = MediaIoBaseUpload(io.FileIO(file_path, 'rb'), mimetype='image/jpeg')
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        ).execute()
        print('File uploaded. File ID:', file.get('id'))
        return file.get('id')


def upload_picture(file_name, folder_id):
    """Function to upload a picture to a specified folder in Google Drive."""
    uploader = GoogleDriveUploader()
    file_path = os.path.join(os.getcwd(), file_name)  # Assumes file is in the current working directory
    return uploader.upload_file(file_path, folder_id)
