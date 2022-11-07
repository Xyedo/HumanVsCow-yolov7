import cv2
import firebase_admin
from threading import Lock
import numpy
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from datetime import datetime
import utils.realtime_db_firebase.constant as constant
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
        self._alarm_ref = db.reference("alarm")
        self._alarm_locker = Lock()
        self._is_alarm_on = False
        self._bucket = storage.bucket()
        self._img_locker = Lock()
        self._interference_locker = Lock()
        self._is_add_img_finish = True
        self._is_add_interference_finish = True

    def is_interference_upload_finish(self):
        with self._interference_locker:
            return self._is_add_interference_finish

    def is_img_upload_finish(self):
        with self._img_locker:
            return self._is_add_img_finish

    def _set_interference_finish(self, val: bool):
        with self._interference_locker:
            self._is_add_interference_finish = val

    def _set_img_finish(self, val: bool):
        with self._img_locker:
            self._is_add_img_finish = val

    def save_interference(self, conf: float):
        self._set_interference_finish(False)
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        self._human_ref_json.push().set({
            'isHuman': conf,
            'detectedDate': now
        })
        self._set_interference_finish(True)

    def _add_image_json(self, public_url: str):
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        self._human_ref_img.push().set({
            'imgUrl': public_url,
            'capturedDate': now
        })

    def add_image(self, file: numpy.ndarray):
        self._set_img_finish(False)
        now = datetime.now()
        blob = self._bucket.blob(f'monitor/{now}')
        with TemporaryFile() as temp:
            filename_temp = "".join([str(temp.name), ".jpg"])
            cv2.imwrite(filename_temp, file)
            blob.upload_from_filename(filename_temp, content_type='image/jpeg')
            blob.make_public()
            self._add_image_json(blob.public_url)

        self._set_img_finish(True)

    def check_alarm(self):
        with self._alarm_locker:
            self._is_alarm_on = self._alarm_ref.get()

    def is_alarm_on(self) -> bool:
        with self._alarm_locker:
            return self._is_alarm_on
