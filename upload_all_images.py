import os
import io
import json
import logging
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Load configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)


class GoogleDriveUploader:
    def __init__(self):
        self.scopes = config["google_drive"]["scopes"]
        self.token_path = config["google_drive"]["token_path"]
        self.credentials_file = config["google_drive"]["credentials_file"]
        self.default_folder_id = config["google_drive"]["default_folder_id"]
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
                from google_auth_oauthlib.flow import InstalledAppFlow
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes)
                creds = flow.run_local_server(port=0)
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        return creds

    def upload_file(self, file_path, folder_id=None, file_name=None):
        """Upload a file to a specified folder on Google Drive."""
        if not folder_id:
            folder_id = self.default_folder_id
            
        if not file_name:
            file_name = os.path.basename(file_path)
            
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        # Determine MIME type based on file extension
        file_extension = os.path.splitext(file_path)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp'
        }
        mime_type = mime_types.get(file_extension, 'application/octet-stream')
        
        try:
            media = MediaIoBaseUpload(io.FileIO(file_path, 'rb'), mimetype=mime_type)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id',
                supportsAllDrives=True
            ).execute()
            
            logging.info(f'File uploaded successfully: {file_name} (ID: {file.get("id")})')
            return file.get('id')
            
        except Exception as e:
            logging.error(f'Failed to upload {file_name}: {str(e)}')
            return None

    def get_pictures_directory(self):
        """Get the pictures directory path - looking in /home/lol/Pictures"""
        # Since you're running from /home/lol/, we can use the home directory
        home_dir = os.path.expanduser('~')
        pictures_path = os.path.join(home_dir, 'Pictures')
        
        # Alternative: Use absolute path directly
        # pictures_path = '/home/lol/Pictures'
        
        logging.info(f"Looking for pictures in: {pictures_path}")
        return pictures_path

    def upload_all_images(self, pictures_path=None):
        """Upload all images from the pictures directory and subdirectories."""
        if not pictures_path:
            pictures_path = self.get_pictures_directory()
            
        if not os.path.exists(pictures_path):
            logging.error(f"Pictures directory does not exist: {pictures_path}")
            return False
            
        # Supported image extensions
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        uploaded_count = 0
        failed_count = 0
        
        logging.info(f"Starting upload of all images from: {pictures_path}")
        
        # Walk through all subdirectories
        for root, dirs, files in os.walk(pictures_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                if file_ext in image_extensions:
                    logging.info(f"Uploading: {file_path}")
                    
                    # Create a relative path for the filename to maintain folder structure
                    relative_path = os.path.relpath(file_path, pictures_path)
                    upload_name = relative_path.replace(os.path.sep, '_')
                    
                    result = self.upload_file(file_path, file_name=upload_name)
                    if result:
                        uploaded_count += 1
                    else:
                        failed_count += 1
        
        logging.info(f"Upload completed: {uploaded_count} successful, {failed_count} failed")
        return uploaded_count > 0

    def upload_recent_images(self, days=1, pictures_path=None):
        """Upload images from the last X days."""
        if not pictures_path:
            pictures_path = self.get_pictures_directory()
            
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
        uploaded_count = 0
        failed_count = 0
        
        logging.info(f"Uploading images from the last {days} day(s) from: {pictures_path}")
        
        for root, dirs, files in os.walk(pictures_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                if file_ext in image_extensions:
                    # Check file modification time
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_mtime >= cutoff_date:
                        logging.info(f"Uploading recent image: {file_path}")
                        
                        relative_path = os.path.relpath(file_path, pictures_path)
                        upload_name = relative_path.replace(os.path.sep, '_')
                        
                        result = self.upload_file(file_path, file_name=upload_name)
                        if result:
                            uploaded_count += 1
                        else:
                            failed_count += 1
        
        logging.info(f"Recent upload completed: {uploaded_count} successful, {failed_count} failed")
        return uploaded_count > 0


def upload_all_pictures():
    """Main function to upload all pictures to Google Drive."""
    try:
        uploader = GoogleDriveUploader()
        success = uploader.upload_all_images()
        
        if success:
            logging.info("All pictures uploaded successfully!")
            return True
        else:
            logging.warning("Some pictures failed to upload")
            return False
            
    except Exception as e:
        logging.error(f"Failed to upload pictures: {str(e)}")
        return False


def upload_recent_pictures(days=1):
    """Function to upload recent pictures from the last X days."""
    try:
        uploader = GoogleDriveUploader()
        success = uploader.upload_recent_images(days=days)
        
        if success:
            logging.info(f"Recent pictures from last {days} day(s) uploaded successfully!")
            return True
        else:
            logging.warning("Some recent pictures failed to upload")
            return False
            
    except Exception as e:
        logging.error(f"Failed to upload recent pictures: {str(e)}")
        return False


if __name__ == "__main__":
    # When run directly, upload all pictures
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload pictures to Google Drive')
    parser.add_argument('--recent', type=int, help='Upload only pictures from the last X days')
    
    args = parser.parse_args()
    
    if args.recent:
        upload_recent_pictures(days=args.recent)
    else:
        upload_all_pictures()