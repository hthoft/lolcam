from flask import Flask, redirect, request, render_template, jsonify
from time import sleep


app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route("/initate", methods=['POST', 'GET'])
def initate():
    print("Starter cam")
    sleep(5)
    return jsonify({'hide': True})

if __name__ == '__main__':
    #from waitress import serve
    #serve(app, host="0.0.0.0", port=8080)
    try: 
        app.run(host='0.0.0.0', port=50005, debug=True, use_reloader=False)
    finally:
        pass