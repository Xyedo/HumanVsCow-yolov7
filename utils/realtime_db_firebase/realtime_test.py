import threading
import time
import unittest
from realtime import Realtime
from PIL import Image
import numpy
import cv2


class RealtimeDBTestCase(unittest.TestCase):
    def setUp(self):
        self.rt = Realtime()
        self.assertIsInstance(self.rt, Realtime, 'Realtime.setUp : object is not instantiated')

    def testAddLog(self):
        self.rt.save_interference(0.5)

    def testAddImage(self):
        img = Image.open("C:/Users/ACER/Projects/TA/DataSet/Cuplikan layar 2022-12-02 173325.jpg")
        np_img = numpy.asarray(img)
        self.rt.add_image(np_img)

    def testCheckAlarm(self):
        self.rt.check_alarm()
        self.assertTrue(self.rt.is_alarm_on())

    def testCheckAlarmConn(self):
        ts_alarm = []
        for i in range(10):
            t1 = threading.Thread(target=self.rt.check_alarm, args=())
            ts_alarm.append(t1)
            t1.start()
            time.sleep(2)
            self.assertTrue(self.rt.is_alarm_on())
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
