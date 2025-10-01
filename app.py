import os
import logging
import json
import socket
# Configure logging
LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), '/home/lol/logs', 'application.log')
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)  # Ensure the logs directory exists

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler()
    ]
)

# Load configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

logging.info("Configuration loaded successfully")

import time
from datetime import datetime, timedelta
from flask import Flask, request, render_template, jsonify, Response
from picamera2 import Picamera2
import cv2
from PIL import Image
from drive_uploader import upload_picture
from drive_folder import create_folder_in_drive
import serial

app = Flask(__name__)

# Global variables for network status
network_available = False
offline_mode = True
folder_id = None

def check_internet():
    """Simple one-time internet check at startup."""
    try:
        socket.setdefaulttimeout(5)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(('8.8.8.8', 53))
        logging.info("Internet connection verified")
        return True
    except Exception as e:
        logging.warning(f"No internet connection: {e}")
        return False

def test_network_at_startup():
    """Test network connectivity once at startup"""
    global network_available, offline_mode
    
    logging.info("Testing network connectivity at startup...")
    network_available = check_internet()
    offline_mode = not network_available
    
    if network_available:
        logging.info("Network available - Online mode")
    else:
        logging.warning("No network - Offline mode")
    
    return network_available

# Initialize PiCamera and Serial
try:
    picam2 = Picamera2()
    preview_config = picam2.create_preview_configuration(main={"size": tuple(config["camera"]["preview_size"])})
    capture_config = {"main": {"size": tuple(config["camera"]["capture_size"])}}
    picam2.configure(preview_config)
    picam2.start()
    logging.info("PiCamera initialized and started")
except Exception as e:
    logging.error(f"Error initializing PiCamera: {e}")
    raise

try:
    ser = serial.Serial(config["serial"]["port"], config["serial"]["baud_rate"], timeout=config["serial"]["timeout"])
    time.sleep(2)
    logging.info("Serial communication initialized")
except Exception as e:
    logging.error(f"Error initializing serial communication: {e}")
    raise

# Preload the overlay image
try:
    overlay_image = Image.open(config["overlay"]["file_path"])
    logging.info("Overlay image loaded")
except Exception as e:
    logging.error(f"Error loading overlay image: {e}")
    raise

def apply_zoom():
    """Apply zoom based on the zoom level from the config."""
    try:
        zoom_level = config["camera"]["zoom_level"]
        sensor_size = picam2.sensor_resolution
        width, height = sensor_size
        new_width = int(width / zoom_level)
        new_height = int(height / zoom_level)
        x_offset = (width - new_width) // 2
        y_offset = (height - new_height) // 2
        crop_rect = (x_offset, y_offset, new_width, new_height)
        picam2.set_controls({"ScalerCrop": crop_rect})
        logging.info("Zoom applied")
    except Exception as e:
        logging.error(f"Error applying zoom: {e}")

def create_picture_folder():
    """Create a folder for saving pictures."""
    try:
        pictures_dir = config["directories"]["pictures_path"]
        current_date = datetime.now().strftime("%Y-%m-%d")
        folder_path = os.path.join(pictures_dir, current_date)
        os.makedirs(folder_path, exist_ok=True)
        logging.info(f"Created folder: {folder_path}")
    except Exception as e:
        logging.error(f"Error creating picture folder: {e}")
        raise

@app.route('/')
def home():
    logging.info("Home endpoint accessed")
    return render_template('index.html')

@app.route("/initiate", methods=['POST', 'GET'])
def initiate():
    logging.info("Initiate endpoint accessed")
    time.sleep(5)
    return jsonify({'hide': True})

@app.route("/capture", methods=['GET'])
def capture():
    global folder_id, offline_mode
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.info("Capture endpoint accessed")
    
    try:
        filename = f"{config['directories']['pictures_path']}/{datetime.now().strftime('%Y-%m-%d')}/{current_datetime}.jpg"
        
        # Send serial signal
        try:
            ser.write(b'1')
            time.sleep(0.5)
            logging.info("Serial signal sent")
        except Exception as e:
            logging.error(f"Error sending serial signal: {e}")

        # Capture and save photo
        picam2.capture_file(filename)
        logging.info(f"Photo captured and saved to {filename}")

        # Apply overlay
        base_image = Image.open(filename)
        base_image.paste(overlay_image, (0, 0), overlay_image)
        base_image.save(filename)
        logging.info("Overlay applied to the photo")

        # If online mode, try to upload
        if not offline_mode:
            try:
                folder_id = create_folder_in_drive()
                upload_picture(filename, folder_id)
                logging.info("Photo uploaded to Drive")
                return jsonify({
                    "success": True, 
                    "message": "Photo captured and uploaded successfully.",
                    "url": config['drive']['base_url'] + folder_id,
                    "offline_mode": False
                })
            except Exception as e:
                logging.error(f"Upload failed: {e}")
                # Fall through to offline mode if upload fails
        
        # Offline response - this is the normal flow when offline
        logging.info("Photo saved locally (offline mode)")
        return jsonify({
            "success": True, 
            "message": "Photo captured and saved locally.",
            "offline_mode": True,
            "offline_message": config['offline_mode']['message']
        })
        
    except Exception as e:
        logging.error(f"Error capturing photo: {e}")
        # Only return error message for actual capture failures, not offline mode
        return jsonify({
            "success": False, 
            "message": str(e),
            "offline_mode": offline_mode
        }), 500

@app.route("/capture_next", methods=['GET'])
def capture_next():
    global offline_mode
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.info("Capture Next endpoint accessed")
    
    try:
        filename = f"{config['directories']['pictures_path']}/{datetime.now().strftime('%Y-%m-%d')}/{current_datetime}.jpg"
        
        # Send serial signal
        try:
            ser.write(b'1')
            time.sleep(0.5)
            logging.info("Serial signal sent")
        except Exception as e:
            logging.error(f"Error sending serial signal: {e}")

        # Capture and save photo
        picam2.capture_file(filename)
        logging.info(f"Photo captured and saved to {filename}")

        # Apply overlay
        base_image = Image.open(filename)
        base_image.paste(overlay_image, (0, 0), overlay_image)
        base_image.save(filename)
        logging.info("Overlay applied to the photo")

        # If online mode and we have a folder_id, try to upload
        if not offline_mode and folder_id:
            try:
                upload_picture(filename, folder_id)
                logging.info("Photo uploaded to Drive")
                return jsonify({
                    "success": True, 
                    "message": "Photo captured and uploaded successfully.",
                    "url": config['drive']['base_url'] + folder_id,
                    "offline_mode": False
                })
            except Exception as e:
                logging.error(f"Upload failed: {e}")
        
        # Offline response - this is the normal flow when offline
        logging.info("Photo saved locally (offline mode)")
        return jsonify({
            "success": True, 
            "message": "Photo captured and saved locally.",
            "offline_mode": True,
            "offline_message": config['offline_mode']['message']
        })
        
    except Exception as e:
        logging.error(f"Error capturing photo: {e}")
        # Only return error message for actual capture failures, not offline mode
        return jsonify({
            "success": False, 
            "message": str(e),
            "offline_mode": offline_mode
        }), 500

@app.route("/capture_next", methods=['GET'])
def capture_next():
    global offline_mode
    current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    logging.info("Capture Next endpoint accessed")
    
    try:
        filename = f"{config['directories']['pictures_path']}/{datetime.now().strftime('%Y-%m-%d')}/{current_datetime}.jpg"
        
        # Send serial signal
        try:
            ser.write(b'1')
            time.sleep(0.5)
            logging.info("Serial signal sent")
        except Exception as e:
            logging.error(f"Error sending serial signal: {e}")

        # Capture and save photo
        picam2.capture_file(filename)
        logging.info(f"Photo captured and saved to {filename}")

        # Apply overlay
        base_image = Image.open(filename)
        base_image.paste(overlay_image, (0, 0), overlay_image)
        base_image.save(filename)
        logging.info("Overlay applied to the photo")

        # If online mode and we have a folder_id, try to upload
        if not offline_mode and folder_id:
            try:
                upload_picture(filename, folder_id)
                logging.info("Photo uploaded to Drive")
                return jsonify({
                    "success": True, 
                    "message": "Photo captured and uploaded successfully.",
                    "url": config['drive']['base_url'] + folder_id,
                    "offline_mode": False
                })
            except Exception as e:
                logging.error(f"Upload failed: {e}")
        
        # Offline response
        logging.info("Photo saved locally")
        return jsonify({
            "success": True, 
            "message": "Photo captured and saved locally.",
            "offline_mode": True,
            "offline_message": config['offline_mode']['message']
        })
        
    except Exception as e:
        logging.error(f"Error capturing photo: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/settings', methods=['POST'])
def settings():
    logging.info("Settings endpoint accessed")
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
        logging.info("Settings saved successfully")
        return jsonify({'success': True, 'message': 'Changes saved successfully'}), 200
    except Exception as e:
        logging.error(f"Error in settings endpoint: {e}")
        return jsonify({'success': False, 'message': f"Error: {e}"}), 500

@app.route('/video')
def video():
    logging.info("Video endpoint accessed")
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/send_pulse')
def send_pulse():
    logging.info("Send Pulse endpoint accessed")
    try:
        ser.write(b'1')
        logging.info("Pulse sent successfully")
        return "Pulse sent!"
    except Exception as e:
        logging.error(f"Failed to send pulse: {e}")
        return f"Failed to send pulse: {e}"

def generate_frames():
    logging.info("Generating video frames")
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
        logging.info("Application starting")
        create_picture_folder()
        apply_zoom()
        
        # Test network connectivity once at startup
        test_network_at_startup()
        
        app.run(host=config["app"]["host"], port=config["app"]["port"], debug=config["app"]["debug"], use_reloader=False)
    finally:
        picam2.stop()
        logging.info("Application stopped")
