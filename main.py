from flask import Flask, send_file, abort, request
from flask_socketio import SocketIO, emit, join_room
from flask_cors import CORS
import io, base64
from PIL import Image
import secrets
import os

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

gauth = GoogleAuth(settings={
    "client_config_backend": "service",
    "service_config": {
        "client_json_file_path": "service-secrets.json",
    }
})
# Authenticate
gauth.ServiceAuth()
drive = GoogleDrive(gauth)


app = Flask(__name__)
CORS(app)
app.config['validLinks'] = []

app.config['PASSWORD'] = "234123"
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")


def getSortedPhotos():
    photos = os.listdir("tempPhotos")
    photos = [os.path.join('tempPhotos', f) for f in photos]
    photos.sort(key=os.path.getctime)
    fphotos = []
    for photo in photos:
        if "_noConsent" not in photo:
            fphotos.insert(0, os.path.splitext(photo.replace('tempPhotos/', ""))[0])
    return fphotos

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
        if not data['givenConsent']:
            photoID += "_noConsent"
        img = Image.open(io.BytesIO(base64.decodebytes(bytes(data['photo'], "utf-8"))))
        img.save(f'tempPhotos/{photoID}.png')
        if  data['givenConsent']:
            photo = drive.CreateFile({'title': photoID, "parents": [{"id": "1kGeEKc1uC2547CDLDh1fDbxP_DcvM2Dd"}]})
            photo.SetContentFile(f'tempPhotos/{photoID}.png')
            photo.Upload()
        app.config['validLinks'].append(photoID)
        emit("uploadPhoto", {'status': 'success', 'photoID': photoID})
        emit("updateScreen", {'photos': getSortedPhotos()}, to="screenRoom")
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

@app.route('/getDirectPhoto/<photoID>')
def getDirectPhoto(photoID):
    if request.args['password'] == app.config['PASSWORD']:
        return send_file(f"tempPhotos/{photoID}.png")

@socketio.on('connectScreen')
def connectScreen(data):
    if data['password'] == app.config['PASSWORD']:
        join_room("screenRoom")
        emit("connectScreen", {'status': 'success', 'photos': getSortedPhotos()})
    else:
        emit("connectScreen", {'status': 'error'})


@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    print("Starting server...")
    if not os.path.exists("tempPhotos"):
        os.makedirs("tempPhotos")
    socketio.run(app, host="0.0.0.0", port=5671)