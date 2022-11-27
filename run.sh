#!/bin/bash

runDet() {
	 source "/home/xyedo/project/python/python-venv/yolov7/bin/activate"
	 cd  "/home/xyedo/project/python/HumanVsCow-yolov7"
	 python ./dethumanvscow.py --weights ./best.pt --source "v4l2src device=/dev/video0 ! video/x-raw, format= GRAY8 ! videoconvert ! appsink max-buffers=1 drop=true " --alarm --connect-rtdb

}

wifiCurrCon=$(nmcli -t -f active,ssid dev wifi | egrep '^yes' | cut -d\: -f2)

echo "$wifiCurrCon"

if [ "$wifiCurrCon" == "King" ]
then
       	echo "Curr wifi is expected"
else 
	if [ -n "$wifiCurrCon" ]; then
		echo "Curr wifi is not expected"
		nmcli conn down "$wifiCurrCon"
	fi
	while true; do
		nmcli con up "King";conUp=$?
		if [ $conUp -eq 0 ]; then
			break
		else
			echo "cannot connect to the expected Wifi, retrying in 5s..."
			sleep 5s
		fi
	done	
fi
runDet
