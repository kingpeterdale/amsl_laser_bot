from threading import Thread, Lock
import cv2
import time
import math

class CameraTracker:
    def __init__(self):
        
        # Capture parametrs
        self.url = "rtsp://admin:AMCAMSL7248@192.168.168.222/Preview_01_sub"
        self.gs_pipeline = (
            f"rtspsrc location={self.url} latency=0 ! "
            "rtph264depay ! "
            "avdec_h264 ! "
            "videoconvert ! "
            "video/x-raw,format=(string)BGR ! "
            "appsink drop=1"
        )
        self.cap = cv2.VideoCapture(self.gs_pipeline, cv2.CAP_GSTREAMER)
        assert self.cap.isOpened()

        #ARUCO detection
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.aruco_detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
        self.locate_thread = Thread(target=self.locate, daemon=True)
        self.latest_pose = None
        self.pose_lock = Lock()

        # Camera capture
        self.running = False
        self.capture_thread = Thread(target=self.capture, daemon=True)
        self.latest_frame = None
        self.frame_count = 0
        self.frame_lock = Lock()


    def capture(self):
        ''' Reads camera frames in own Thread'''
        
        print('Capture thread starting ....')
        while self.running:
            ret,img = self.cap.read()
            if ret:
                with self.frame_lock:
                    self.latest_frame = img
                    self.frame_count += 1
                #print(f'CAPTURED {self.frame_count}')
            time.sleep(0.01)
        print('Capture thread ending')


    def locate(self):
        ''' Dectects marker and calculates pose in own Thread '''

        print('Locate thread starting ...')
        last_count = 0
        while self.running:
            img = None
            with self.frame_lock:
                # wait for new frame
                if self.frame_count > last_count:
                    img = self.latest_frame.copy()
                    last_count = self.frame_count
            if img is not None:
                # detect marker
                corners, ids, _ = self.aruco_detector.detectMarkers(img)
                if len(corners) > 0:
                    ids = ids.flatten()
                    for id,corner in zip(ids,corners):
                        if id == 0:
                            corner = corner.reshape((4,2))
                            x,y, hdg = self.calc_pose(corner)
                            print(f'[0] POS:{x:.1f},{y:.1f} HDG:{hdg:.1f} FRM:{last_count}')
                            with self.pose_lock:
                                self.latest_pose = [x,y,hdg]
            time.sleep(0.1)
        print('Locate thread ending')


    def calc_pose(self,corners):
        x0,y0 = corners[0]
        x2,y2 = corners[2]
        x3,y3 = corners[3]
        heading = 90. - math.degrees(math.atan2(-(y0-y3),x0-x3))
        x_avg = (x0 + x2)/2.
        y_avg = (y0 + y2)/2.
        return x_avg, y_avg, heading


    def start(self):
        ''' Starts capture and locate threads '''
        self.running = True
        self.capture_thread.start()
        self.locate_thread.start()


    def stop(self):
        ''' Stops capture and locate threads '''
        self.running = False
        self.capture_thread.join()
        self.locate_thread.join()


    def latest(self):
        ret_img = None
        ret_pose = None
        if self.latest_frame is not None:
            with self.frame_lock:
                ret_img =  self.latest_frame.copy()
        
        if self.latest_pose is not None:
            with self.pose_lock:
                ret_pose = self.latest_pose.copy()
        return ret_img, ret_pose
        
    

if __name__ == '__main__':
    tracker = CameraTracker()
    tracker.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(e)

    tracker.stop()