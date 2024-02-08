import os
import io
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Define the scopes for Drive API
SCOPES = ['https://www.googleapis.com/auth/drive']

# Path to the token.json file
TOKEN_PATH = 'token.json'

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

def create_folder(service, parent_folder_id, folder_name):
    """Create a folder inside a parent folder."""
    file_metadata = {
        'name': folder_name,
        'parents': [parent_folder_id],
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    return folder.get('id')

def create_subfolder(service, parent_folder_id, subfolder_name):
    """Create a subfolder inside a parent folder."""
    folder_id = create_folder(service, parent_folder_id, subfolder_name)
    return folder_id

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
        fields='id, webViewLink',
        supportsAllDrives=True
    ).execute()
    print('Picture uploaded. File ID:', file.get('id'))
    return file.get('webViewLink')

def main():
    # Authenticate
    creds = authenticate()
    # Build the Drive API service
    service = build('drive', 'v3', credentials=creds)
    # Create the initial folder with an ID
    initial_folder_id = '13dQff2uQ65XAKVc9CRZcNXnkUZwzTgzX'
    # Create a folder with a unique name inside the initial folder
    now = datetime.now()
    folder_name = now.strftime("%Y-%m-%d_%H-%M-%S") + "Session"
    folder_id = create_folder(service, parent_folder_id=initial_folder_id, folder_name=folder_name)
    # Create a subfolder with the current time and seconds inside the created folder
    subfolder_name = now.strftime("%H-%M-%S") + "_"
    subfolder_id = create_subfolder(service, parent_folder_id=folder_id, subfolder_name=subfolder_name)
    # Example picture file to upload
    picture_path = 'IMG_1935.JPEG'
    picture_name = 'IMG_1935.JPEG'
    # Upload the picture to the subfolder
    picture_link = upload_picture(service, subfolder_id, picture_path, picture_name)
    print("Uploaded picture link:", picture_link)

if __name__ == '__main__':
    main()
