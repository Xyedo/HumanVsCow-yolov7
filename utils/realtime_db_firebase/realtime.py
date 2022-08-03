import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import firestore
from firebase_admin import storage
from datetime import datetime
import constant

path = constant.PATH


class Realtime:
    def __int__(self):
        cred = credentials.Certificate(path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': constant.DATABASE_URL,
            'storageBucket': constant.STORAGE_BUCKET
        })
        self._human_ref_json = db.reference('check/is-human/posts')
        self._human_ref_img = db.reference('monitor/posts')
        self._bucket = storage.bucket()

    def save_interference(self, conf):
        self._human_ref_json.push().set({
            'isHuman': conf,
            'detectedDate': firestore.SERVER_TIMESTAMP
        })

    def _add_image_json(self, public_url: str):
        self._human_ref_img.push().set({
            'imgUrl': public_url
        })

    def add_image(self, file):
        now = datetime.now()
        blob = self._bucket.blob(f'monitor/{now}', chunk_size=262144)
        blob.upload_from_file(file)
        blob.make_public()
        self._add_image_json(blob.public_url)
