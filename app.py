from flask import Flask, request, render_template, jsonify, Response
from picamera2 import Picamera2, Preview
from datetime import datetime, timedelta
import json
import time
import cv2
import numpy as np
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload
import wifi
import io
import os
from PIL import Image
from drive_uploader import upload_picture
from drive_folder import create_folder_in_drive
import serial
#import rpi.GPIO

app = Flask(__name__)

# Initialize the Pi Camera
picam2 = Picamera2()

preview_config = picam2.create_preview_configuration(main={"size": (1920, 1080)})
capture_config = {"main": {"size": (1920, 1080)}}  # 1080p capture configuration
picam2.configure(preview_config)
picam2.start()
folder_id = None
filename = None
url = "https://drive.google.com/drive/folders/"


ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
time.sleep(2)

def create_picture_folder():
    # Define the path for the folder
    pictures_dir = "/home/lol/Pictures"
    current_date = datetime.now().strftime("%Y-%m-%d")
    folder_path = os.path.join(pictures_dir, current_date)
    
    # Create the folder if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created folder: {folder_path}")


@app.route('/')
def home():
    return render_template('index.html')

@app.route("/initiate", methods=['POST', 'GET'])
def initiate():
    print("Starting cam")
    time.sleep(5)  # Use time.sleep for delays
    return jsonify({'hide': True})


@app.route("/capture", methods=['GET'])
def capture():
    global folder_id
    global filename
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    try:
        # Capture the image
        filename = f"Pictures/{datetime.now().strftime('%Y-%m-%d')}/{current_datetime}.jpg"
        try:
            ser.write(b'1')
            time.sleep(0.5)
        except:
            pass
        picam2.capture_file(filename)

        base_image = Image.open(filename)
        overlay_image = Image.open('overlay2.png')
        base_image.paste(overlay_image, (0, 0), overlay_image)
        base_image.save(filename)

        folder_id = create_folder_in_drive()
        upload_picture(filename, folder_id)
        return jsonify({"success": True, "message": "Photo captured and uploaded successfully.", "url": str(url+folder_id)})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/capture_next", methods=['GET'])
def capture_next():
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    try:
        # Capture the image
        filename = f"Pictures/{datetime.now().strftime('%Y-%m-%d')}/{current_datetime}.jpg"
        try:
            ser.write(b'1')  # Send a byte
            time.sleep(0.5)
        except:
            pass
        picam2.capture_file(filename)  # Specify capture configuration here if needed
        base_image = Image.open(filename)
        overlay_image = Image.open('overlay.png')
        base_image.paste(overlay_image, (0, 0), overlay_image)
        base_image.save(filename)
        upload_picture(filename, folder_id)
        return jsonify({"success": True, "message": "Photo captured and uploaded successfully.", "url": str(url+folder_id)})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500 
     

@app.route('/settings', methods=['POST'])
def settings():
    try:
        data = request.get_json()
        selected_ssid = "AAU-1-DAY"
        wifi_password1 = data.get('wifiPassword')  # Corrected variable name
        wifi_password2 = data.get('wifiPassword2')

        # Constructing the data dictionary
        data = {
            (datetime.now()).strftime("%Y-%m-%d"): {"ssid": selected_ssid, "password": wifi_password1},  # Corrected variable name
            (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"): {"ssid": "AAU-1-DAY", "password": wifi_password2}
        }

        # Writing the data to a JSON file
        with open("lolcam/network.json", "w") as json_file:
            json.dump(data, json_file, indent=4)

        response_data = {'success': True, 'message': 'Changes saved successfully'}
        return jsonify(response_data), 200
    except Exception as e:
        error_message = 'An error occurred. Please try again.'
        print("Error:", e)
        return jsonify({'success': False, 'message': error_message}), 500

# Stream the camera feed
@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/send_pulse')
def send_pulse():
    try:
        ser.write(b'1')  # Send a byte
        return "Pulse sent!"
    except:
        return "Failed to send pulse"

def generate_frames():
    while True:
        frame = picam2.capture_array()  # Capture frame as a numpy array
        # Convert the color space from BGR (OpenCV default) to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Encode the frame in JPEG format
        (flag, encodedImage) = cv2.imencode(".jpg", frame)
        if not flag:
            continue
        # Yield the encoded frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')



if __name__ == '__main__':
    try:
        create_picture_folder()
        app.run(host='0.0.0.0', port=50005, debug=True, use_reloader=False)
    finally:
        picam2.stop()  # Ensure the camera is stopped
