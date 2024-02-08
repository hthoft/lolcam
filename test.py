
from drive_uploader import upload_picture
from drive_folder import create_folder_in_drive

folder_id = create_folder_in_drive()
filename =  "IMG_1935.JPEG"

upload_picture(filename, folder_id)
