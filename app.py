from flask import Flask, request, render_template, jsonify, Response
from picamera2 import Picamera2
from datetime import datetime
import time
import cv2
import numpy as np
import wifi
import io
import os

app = Flask(__name__)

# Initialize the Pi Camera
picam2 = Picamera2()
preview_config = picam2.create_preview_configuration(main={"size": (1280, 800)})
picam2.configure(preview_config)
picam2.start()


@app.before_first_request
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
    try:
        picam2.capture_file("Pictures/" + str(datetime.now().minute) + ".jpg")
        return jsonify({"success": True, "message": "Photo captured and saved successfully."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/settings", methods=['GET', 'POST'])
def settings():
    if request.method == 'GET':
        scanner = wifi.Cell.all('wlan0')
        networks = [(cell.signal, cell.ssid) for cell in scanner]
        return jsonify(networks)
    elif request.method == 'POST':
        selected_ssid = request.form['ssidSelection']
        password = request.form['wifiPassword']
        try:
            for cell in scanner:
                if cell.ssid == selected_ssid:
                    scheme = wifi.Scheme.for_cell('wlan0', cell.ssid, cell, password)
                    scheme.save()
                    scheme.activate()
                    return jsonify({"success": True, "message": "WiFi settings updated successfully."})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 400

# Stream the camera feed
@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

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
        app.run(host='0.0.0.0', port=50005, debug=True, use_reloader=False)
    finally:
        picam2.stop()  # Ensure the camera is stopped
