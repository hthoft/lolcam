import os
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Define the scopes for Drive API
SCOPES = ['https://www.googleapis.com/auth/drive']

# Path to the token.json file
TOKEN_PATH = 'token.json'

# ID of the folder where you want to upload the pictures
FOLDER_ID = '13dQff2uQ65XAKVc9CRZcNXnkUZwzTgzX'

def authenticate():
    """Authenticate using the OAuth2 token."""
    creds = None
    # Check if token.json file exists
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    # If there are no valid credentials, ask the user to log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds

def upload_picture(service, folder_id, picture_path, picture_name):
    """Upload a picture to a folder on Google Drive."""
    file_metadata = {
        'name': picture_name,
        'parents': [folder_id]
    }
    media = MediaIoBaseUpload(io.FileIO(picture_path, 'rb'), mimetype='image/jpeg')
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id',
        supportsAllDrives=True
    ).execute()
    print('Picture uploaded. File ID:', file.get('id'))

def main():
    # Authenticate
    creds = authenticate()
    # Build the Drive API service
    service = build('drive', 'v3', credentials=creds)
    # Example picture file to upload
    picture_path = 'IMG_1935.JPEG'
    picture_name = 'IMG_1935.JPEG'
    # Upload the picture
    upload_picture(service, FOLDER_ID, picture_path, picture_name)

if __name__ == '__main__':
    main()
