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


if __name__ == '__main__':
    unittest.main()
