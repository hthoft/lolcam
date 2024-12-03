import os
import time
import json
from datetime import datetime, timedelta
from flask import Flask, request, render_template, jsonify, Response
from picamera2 import Picamera2
import cv2
from PIL import Image
from drive_uploader import upload_picture
from drive_folder import create_folder_in_drive
import serial

# Load configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

app = Flask(__name__)

# Initialize PiCamera and Serial
picam2 = Picamera2()
preview_config = picam2.create_preview_configuration(main={"size": tuple(config["camera"]["preview_size"])})
capture_config = {"main": {"size": tuple(config["camera"]["capture_size"])}}
picam2.configure(preview_config)
picam2.start()

ser = serial.Serial(config["serial"]["port"], config["serial"]["baud_rate"], timeout=config["serial"]["timeout"])
time.sleep(2)

folder_id = None


def apply_zoom():
    """Apply zoom based on the zoom level from the config."""
    zoom_level = config["camera"]["zoom_level"]
    sensor_size = picam2.sensor_resolution
    width, height = sensor_size
    new_width = int(width / zoom_level)
    new_height = int(height / zoom_level)
    x_offset = (width - new_width) // 2
    y_offset = (height - new_height) // 2
    crop_rect = (x_offset, y_offset, new_width, new_height)
    picam2.set_controls({"ScalerCrop": crop_rect})


def create_picture_folder():
    """Create a folder for saving pictures."""
    pictures_dir = config["directories"]["pictures_path"]
    current_date = datetime.now().strftime("%Y-%m-%d")
    folder_path = os.path.join(pictures_dir, current_date)
    os.makedirs(folder_path, exist_ok=True)
    print(f"Created folder: {folder_path}")


@app.route('/')
def home():
    return render_template('index.html')


@app.route("/initiate", methods=['POST', 'GET'])
def initiate():
    print("Starting cam")
    time.sleep(5)
    return jsonify({'hide': True})


@app.route("/capture", methods=['GET'])
def capture():
    global folder_id
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    try:
        filename = f"{config['directories']['pictures_path']}/{datetime.now().strftime('%Y-%m-%d')}/{current_datetime}.jpg"
        try:
            ser.write(b'1')
            time.sleep(0.5)
        except Exception as e:
            print(f"Error sending serial signal: {e}")

        picam2.capture_file(filename)

        # Overlay handling
        base_image = Image.open(filename)
        overlay_image = Image.open('overlay.png')
        base_image.paste(overlay_image, (0, 0), overlay_image)
        base_image.save(filename)

        folder_id = create_folder_in_drive()
        upload_picture(filename, folder_id)
        return jsonify({"success": True, "message": "Photo captured and uploaded successfully.",
                        "url": config['drive']['base_url'] + folder_id})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/capture_next", methods=['GET'])
def capture_next():
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    try:
        filename = f"{config['directories']['pictures_path']}/{datetime.now().strftime('%Y-%m-%d')}/{current_datetime}.jpg"
        try:
            ser.write(b'1')
            time.sleep(0.5)
        except Exception as e:
            print(f"Error sending serial signal: {e}")

        picam2.capture_file(filename)

        # Overlay handling
        base_image = Image.open(filename)
        overlay_image = Image.open('overlay_dse.png')
        base_image.paste(overlay_image, (0, 0), overlay_image)
        base_image.save(filename)

        upload_picture(filename, folder_id)
        return jsonify({"success": True, "message": "Photo captured and uploaded successfully.",
                        "url": config['drive']['base_url'] + folder_id})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/settings', methods=['POST'])
def settings():
    try:
        data = request.get_json()
        wifi_password1 = data.get('wifiPassword')
        wifi_password2 = data.get('wifiPassword2')

        network_data = {
            datetime.now().strftime("%Y-%m-%d"): {"ssid": config["wifi"]["ssid_default"], "password": wifi_password1},
            (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"): {"ssid": config["wifi"]["ssid_default"],
                                                                        "password": wifi_password2}
        }

        with open("network.json", "w") as json_file:
            json.dump(network_data, json_file, indent=4)

        return jsonify({'success': True, 'message': 'Changes saved successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f"Error: {e}"}), 500


@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/send_pulse')
def send_pulse():
    try:
        ser.write(b'1')
        return "Pulse sent!"
    except Exception as e:
        return f"Failed to send pulse: {e}"


def generate_frames():
    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        flag, encodedImage = cv2.imencode(".jpg", frame)
        if not flag:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')


if __name__ == '__main__':
    try:
        create_picture_folder()
        apply_zoom()
        app.run(host=config["app"]["host"], port=config["app"]["port"], debug=config["app"]["debug"], use_reloader=False)
    finally:
        picam2.stop()
