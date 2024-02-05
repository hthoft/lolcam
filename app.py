from flask import Flask, render_template, jsonify, Response
from picamera2 import Picamera2
import time

app = Flask(__name__)

# Initialize the Pi Camera
picam2 = Picamera2()
preview_config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(preview_config)
picam2.start()

@app.route('/')
def home():
    return render_template('index.html')

@app.route("/initiate", methods=['POST', 'GET'])
def initiate():
    print("Starting cam")
    time.sleep(5)  # Corrected sleep function call
    return jsonify({'hide': True})

# Stream the camera feed
@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_frames():
    while True:
        frame = picam2.capture_array()  # Capture frame as a numpy array
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame.tobytes() + b'\r\n')

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=50005, debug=True, use_reloader=False)
    finally:
        picam2.stop()  # Ensure the camera is stopped
