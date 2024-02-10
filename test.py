
from drive_uploader import upload_picture
from drive_folder import create_folder_in_drive
from PIL import Image


filename = f"2024-02-09_13-57-48.jpg"
base_image = Image.open(filename)
overlay_image = Image.open('overlay.png')
base_image.paste(overlay_image, (0, 0), overlay_image)
base_image.save(filename)
folder_id = create_folder_in_drive()
upload_picture(filename, folder_id)

url = "https://drive.google.com/drive/folders/"

print(url+folder_id)