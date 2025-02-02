import argparse
import sys
import threading
import cv2
import torch
import torch.backends.cudnn as cudnn
from numpy import random
from pathlib import Path
from mpyg321.MPyg123Player import PlayerStatus, MPyg123Player
from models.experimental import attempt_load
from utils.datasets import LoadWebcam
from utils.general import check_img_size, xyxy2xywh, increment_path, non_max_suppression, scale_coords, set_logging
from utils.plots import plot_one_box
from utils.torch_utils import select_device, time_synchronized
from utils.realtime_db_firebase.realtime import Realtime


def detect():
    source, weights, save_txt, imgsz = opt.source, opt.weights, opt.save_txt, opt.img_size
    alarm_check = True
    save_dir = Path(increment_path(Path(opt.project) / opt.name, exist_ok=opt.exist_ok))  # increment run
    (save_dir / 'labels' if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir


    # Initialize
    set_logging()
    device = select_device(opt.device)
    half = device.type != 'cpu'  # half precision only supported on CUDA

    # Load model
    model = attempt_load(weights, map_location=device)  # load FP32 model
    stride = int(model.stride.max())  # model stride
    imgsz = check_img_size(imgsz, s=stride)  # check img_size

    if half:
        model.half()  # to FP16

    cudnn.benchmark = True  # set True to speed up constant image size inference
    dataset = LoadWebcam(source, img_size=imgsz, stride=stride)
    fps = dataset.cap.get(cv2.CAP_PROP_FPS)
    w = int(dataset.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(dataset.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    vid_writer = cv2.VideoWriter(str(save_dir / "0.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    try:
        # Get names and colors
        names = model.module.names if hasattr(model, 'module') else model.names
        colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]

        # Run inference
        if device.type != 'cpu':
            model(torch.zeros(1, 3, imgsz, imgsz).to(device).type_as(next(model.parameters())))  # run once

        for path, img, im0s, vid_cap in dataset:
            img = torch.from_numpy(img).to(device)
            img = img.half() if half else img.float()  # uint8 to fp16/32
            img /= 255.0  # 0 - 255 to 0.0 - 1.0
            if img.ndimension() == 3:
                img = img.unsqueeze(0)

            # Inference
            t1 = time_synchronized()
            with torch.no_grad():  # Calculating gradients would cause a GPU memory leak
                pred = model(img, augment=False)[0]
            t2 = time_synchronized()
            if opt.connect_rtdb:
                chk_alarm = threading.Thread(target=realtime.check_alarm, args=())
                chk_alarm.start()
                alarm_check = realtime.is_alarm_on()
                if not alarm_check and alarm.status == PlayerStatus.PLAYING:
                    alarm.stop()

            # Apply NMS
            pred = non_max_suppression(pred, opt.conf_thres, opt.iou_thres, classes=opt.classes, agnostic=False)
            t3 = time_synchronized()

            # Process detections
            for i, det in enumerate(pred):  # detections per image
                p, s, im0, frame = path, '', im0s, getattr(dataset, 'frame', 0)

                if len(det):
                    # Rescale boxes from img_size to im0 size
                    det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()
                    # Print results
                    for c in det[:, -1].unique():
                        n = (det[:, -1] == c).sum()  # detections per class
                        s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string

                    # Write results
                    for *xyxy, conf, cls in reversed(det):
                        if save_txt:  # Write to file
                            pa = Path(p)
                            txt_path = str(save_dir / 'labels' / pa.stem) + f'_{frame}'  # img.txt
                            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
                            xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                            line = (cls, *xywh, conf) if opt.save_conf else (cls, *xywh)  # label format
                            with open(txt_path + '.txt', 'a') as f:
                                f.write(('%g ' * len(line)).rstrip() % line + '\n')

                        label = f'{names[int(cls)]} {conf:.2f}'
                        plot_one_box(xyxy, im0, label=label, color=colors[int(cls)], line_thickness=1)

                        # ---UPLOADING TO FIREBASE REALTIME DB --MOST IMPORTANT THING TO WORK
                        if names[int(cls)] == "Human":

                            if opt.connect_rtdb:
                                if realtime.is_img_upload_finish() and float(conf) > 0.7:
                                    th1 = threading.Thread(target=realtime.add_image, args=(im0,))
                                    ts_img_data.append(th1)
                                    th1.start()

                                if realtime.is_interference_upload_finish():
                                    th2 = threading.Thread(target=realtime.save_interference, args=(float(conf),))
                                    ts_logger.append(th2)
                                    th2.start()
                                if opt.alarm and float(conf) >= 0.5:
                                    if alarm_check:
                                        if alarm.status == PlayerStatus.PLAYING:
                                            continue
                                        alarm.play()
                                    else:
                                        alarm.stop()
                        # --ENDED
                cv2.imshow(p, im0)
                cv2.waitKey(1)

                vid_writer.write(im0)
                print(f'{s}Done. ({(1E3 * (t2 - t1)):.1f}ms) Inference, ({(1E3 * (t3 - t2)):.1f}s) NMS')

    except KeyboardInterrupt:
        dataset.cap.release()
        vid_writer.release()
        cv2.destroyAllWindows()
        print("resource cleaned succesfully")

    if save_txt:
        s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
        print(f"Results saved to {save_dir}{s}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', nargs='+', type=str, default='humanvscow160.pt', help='model.pt path(s)')
    parser.add_argument('--source', type=str, default='0', help='source')  # file/folder, 0 for webcam
    parser.add_argument('--img-size', type=int, default=160, help='inference size (pixels)')
    parser.add_argument('--conf-thres', type=float, default=0.25, help='object confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='IOU threshold for NMS')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
    parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
    parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --class 0, or --class 0 2 3')
    parser.add_argument('--project', default='runs/detect', help='save results to project/name')
    parser.add_argument('--name', default='exp', help='save results to project/name')
    parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
    parser.add_argument('--connect-rtdb', action='store_true', help="connect to realtime database")
    parser.add_argument('--alarm', action='store_true', help='for alarm system')
    opt = parser.parse_args()
    print(opt)
    if opt.connect_rtdb:
        realtime = Realtime()
    ts_img_data = []
    ts_logger = []
    if opt.alarm:
        alarm = MPyg123Player()
        alarm.set_song("./alarm.mp3")
        alarm.set_loop(True)
    with torch.no_grad():
        detect()
    for t in ts_img_data:
        t.join()
    for t in ts_logger:
        t.join()
    sys.exit(0)

