import threading
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

    def testConcurency(self):
        im0 = cv2.imread("test_img.jpg")
        ts_img_data = []
        ts_logger = []
        for i in range(5):
            conf = 0.5
            t1 = threading.Timer(interval=5, function=self.rt.add_image, args=(im0,))
            ts_img_data.append(t1)
            t1.start()
            t2 = threading.Timer(interval=1, function=self.rt.save_interference, args=(conf,))
            ts_logger.append(t2)
            t2.start()
        for t in ts_img_data:
            t.join()
        for t in ts_logger:
            t.join()


if __name__ == '__main__':
    unittest.main()
