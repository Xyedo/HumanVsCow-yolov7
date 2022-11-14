#!/bin/bash

activate() {
	source "/home/xyedo/project/python/python-venv/yolov7/bin/activate"
}
activate
python /home/xyedo/project/python/HumanVsCow-yolov7/dethumanvscow.py --weights best.pt --source "v4l2src device=/dev/video0 ! video/x-raw, format= GRAY8 ! videoconvert ! appsink max-buffers=1 drop=true " --alarm --connect-rtdb
