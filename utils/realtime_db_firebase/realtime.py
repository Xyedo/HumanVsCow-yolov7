import cv2
import firebase_admin
import time
import numpy
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from datetime import datetime
import constant
from tempfile import TemporaryFile


class Realtime:
    def __init__(self):
        cred = credentials.Certificate(constant.PATH)
        firebase_admin.initialize_app(cred, {
            'databaseURL': constant.DATABASE_URL,
            'storageBucket': constant.STORAGE_BUCKET
        })
        self._human_ref_json = db.reference('logging/posts')
        self._human_ref_img = db.reference('monitor/posts')
        self._bucket = storage.bucket()

    def save_interference(self, conf: float):
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        self._human_ref_json.push().set({
            'isHuman': conf,
            'detectedDate': now
        })

    def _add_image_json(self, public_url: str):
        self._human_ref_img.push().set({
            'imgUrl': public_url
        })

    def add_image(self, file: numpy.ndarray):
        now = datetime.now()
        blob = self._bucket.blob(f'monitor/{now}')
        with TemporaryFile() as temp:
            filename_temp = "".join([str(temp.name), ".jpg"])
            cv2.imwrite(filename_temp, file)
            blob.upload_from_filename(filename_temp, content_type='image/jpeg')
            blob.make_public()
            self._add_image_json(blob.public_url)
        time.sleep(5)
