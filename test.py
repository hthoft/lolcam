
from drive_uploader import upload_picture
from drive_folder import create_folder_in_drive

folder_id = create_folder_in_drive()
filename =  "favicon.ico"
upload_picture(filename, folder_id)

url = "https://drive.google.com/drive/folders/"

print(url+folder_id)