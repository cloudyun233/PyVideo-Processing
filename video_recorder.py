# video_recorder.py
import cv2
import os
import time
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
from video_utils import VideoUtils


class VideoRecorder(QObject):
    recording_state_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.cap = None
        self.video_writer = None
        self.previewing = False
        self.recording = False
        self.last_record_time = 0
        self.save_path = os.getcwd()
        self.frame_callback = None
        self.status_callback = None
        self.utils = VideoUtils()
        self.output_format = "mp4"
        self.interval = 60
        self.file_prefix = "video"

    def set_callbacks(self, frame_callback=None, status_callback=None):
        self.frame_callback = frame_callback
        self.status_callback = status_callback

    def get_camera_list(self):
        return self.utils.detect_cameras()

    def set_save_path(self, path):
        if os.path.isdir(path):
            self.save_path = path
            return True
        return False

    def _get_camera_property(self, camera_index, prop_func, default):
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            return default
        value = prop_func(cap)
        cap.release()
        return value

    def get_max_camera_resolution(self, camera_index):
        width = self._get_camera_property(camera_index, 
            lambda c: int(c.get(cv2.CAP_PROP_FRAME_WIDTH)), 640)
        height = self._get_camera_property(camera_index,
            lambda c: int(c.get(cv2.CAP_PROP_FRAME_HEIGHT)), 480)
        return (width, height)

    def start_preview(self, camera_index, width=None, height=None, fps=None):
        if self.previewing:
            return True

        try:
            camera_index = int(camera_index)
        except ValueError:
            self._update_status("请选择有效摄像头")
            return False

        if width is None or height is None:
            width, height = self.get_max_camera_resolution(camera_index)
        fps = fps or self._get_camera_property(camera_index,
            lambda c: c.get(cv2.CAP_PROP_FPS), 30)

        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened() or not self._set_camera_params(width, height, fps):
            self._release_camera()
            self._update_status("无法启动摄像头")
            return False

        self.previewing = True
        self._update_status("预览中")
        return True

    def _set_camera_params(self, width, height, fps):
        return (self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width) and
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height) and
                self.cap.set(cv2.CAP_PROP_FPS, fps))

    def stop_preview(self):
        if self.recording:
            self.stop_recording()
        self.previewing = False
        self._release_camera()
        self._update_status("就绪")

    def _release_camera(self):
        if self.cap:
            self.cap.release()
            self.cap = None

    def start_recording(self, output_format=None, interval=None):
        if not self.cap or self.recording:
            return False

        self.interval = int(interval) if interval else self.interval
        self.output_format = output_format or self.output_format
        self.video_writer = self._create_writer()
        
        if not self.video_writer:
            return False

        self.recording = True
        self.recording_state_changed.emit(True)
        self.last_record_time = time.time()
        self._update_status("录制中")
        return True

    def _create_writer(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.file_prefix}_{timestamp}.{self.output_format}"
        return cv2.VideoWriter(
            os.path.join(self.save_path, filename),
            self.utils.get_fourcc(self.output_format),
            self.cap.get(cv2.CAP_PROP_FPS),
            (int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 
             int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))),
            isColor=True
        )

    def stop_recording(self):
        if not self.recording:
            return False
            
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            
        self.recording = False
        self.recording_state_changed.emit(False)
        self._update_status("预览中")
        return True

    def get_frame(self):
        if not self.previewing or not self.cap:
            return False, None

        ret, frame = self.cap.read()
        if not ret:
            return False, None

        if self.recording:
            self.video_writer.write(frame)
            if time.time() - self.last_record_time >= self.interval:
                if self._rotate_video_file(frame):
                    self.last_record_time = time.time()

        return True, frame

    def _rotate_video_file(self, frame):
        if self.video_writer:
            self.video_writer.release()
        self.video_writer = self._create_writer()
        return self.video_writer and self.video_writer.write(frame)

    def _update_status(self, message):
        if self.status_callback:
            self.status_callback(f"状态：{message}")

    def is_previewing(self):
        return self.previewing

    def is_recording(self):
        return self.recording