from flask import Flask, render_template, jsonify, Response
from picamera2 import PiCamera2, PiCameraMk2Renderer
import time

app = Flask(__name__)

# Initialize the Pi Camera
camera = PiCamera2()

@app.route('/')
def home():
    return render_template('index.html')

@app.route("/initiate", methods=['POST', 'GET'])
def initiate():
    print("Starting cam")
    sleep(5)
    return jsonify({'hide': True})

# Stream the camera feed
@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_frames():
    renderer = PiCameraMk2Renderer(camera)
    camera.start_recording('/dev/null', format='h264', resize=(640, 480))
    camera.start_recording(renderer, format='mjpeg', resize=(640, 480))

    try:
        while True:
            camera.wait_recording(1)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + renderer.frame() + b'\r\n')
    finally:
        camera.stop_recording()

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=50005, debug=True, use_reloader=False)
    finally:
        pass
