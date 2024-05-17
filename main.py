from flask import Flask, send_file, abort
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import io, base64
from PIL import Image
import secrets
import os
import time

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

gauth = GoogleAuth()
gauth.LocalWebserverAuth(port_numbers=[8224])
drive = GoogleDrive(gauth)

for files in os.listdir("tempPhotos"):
    os.remove(f"tempPhotos/{files}")


app = Flask(__name__)
CORS(app)
app.config['validLinks'] = []

app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def hello():
    return 'Hello, World!'

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on("uploadPhoto")
def uploadPhoto(data):
    try:
        photoID = secrets.token_urlsafe(24)
        img = Image.open(io.BytesIO(base64.decodebytes(bytes(data['photo'], "utf-8"))))
        img.save(f'tempPhotos/{photoID}.png')
        photo = drive.CreateFile({'title': photoID, "parents": [{"id": "1kGeEKc1uC2547CDLDh1fDbxP_DcvM2Dd"}]})
        photo.SetContentFile(f'tempPhotos/{photoID}.png')
        photo.Upload()
        app.config['validLinks'].append(photoID)
        emit("uploadPhoto", {'status': 'success', 'photoID': photoID})
        print("===== SUCCESS =====")
    except Exception as error:
        print("===== ERROR ===== \n")
        print(error)
        emit("uploadPhoto", {'status': 'error'})
        print("\n===== END =====")


@app.route('/getPhoto/<photoID>')
def getPhoto(photoID):
    if not photoID in app.config['validLinks']:
        return abort(404)

    return send_file(f"tempPhotos/{photoID}.png")
    
@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5671)