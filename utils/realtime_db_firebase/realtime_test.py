import threading
import time
import unittest
from realtime import Realtime
import cv2


class RealtimeDBTestCase(unittest.TestCase):
    def setUp(self):
        self.rt = Realtime()
        self.assertIsInstance(self.rt, Realtime, 'Realtime.setUp : object is not instantiated')

    def testAddLog(self):
        self.rt.save_interference(0.5)

    def testAddImage(self):
        img = cv2.imread("test_img.jpg")
        self.rt.add_image(img)

    def testCheckAlarm(self):
        self.rt.check_alarm()
        self.assertTrue(self.rt.is_alarm_on())

    def testCheckAlarmConn(self):
        ts_alarm = []
        for i in range(10):
            t1 = threading.Thread(target=self.rt.check_alarm)
            ts_alarm.append(t1)
            t1.start()
        for t in ts_alarm:
            t.join()
    def testConcurency(self):
        im0 = cv2.imread("test_img.jpg")
        ts_img_data = []
        ts_logger = []
        for i in range(5):
            conf = 0.5
            if self.rt.is_img_upload_finish():
                t1 = threading.Thread(target=self.rt.add_image, args=(im0,))
                ts_img_data.append(t1)
                t1.start()
            if self.rt.is_interference_upload_finish():
                t2 = threading.Thread(target=self.rt.save_interference, args=(conf,))
                ts_logger.append(t2)
                t2.start()
            time.sleep(2)

        for t in ts_img_data:
            t.join()
        for t in ts_logger:
            t.join()


if __name__ == '__main__':
    unittest.main()
