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
        self.frame_count = 0
        self.start_time = 0

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
        self.start_time = time.time()
        self.frame_count = 0
        self._update_status("录制中")
        return True

    def _create_writer(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.file_prefix}_{timestamp}.{self.output_format}"
        filepath = os.path.join(self.save_path, filename)
        
        # 确保目录存在
        os.makedirs(self.save_path, exist_ok=True)
        
        # 获取摄像头参数
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"创建视频写入器: {filepath}, {width}x{height}, FPS: {fps}")  # 调试信息
        
        # 确保FPS是合理值
        if fps <= 0:
            fps = 30.0  # 默认值
            
        fourcc = cv2.VideoWriter_fourcc(*self._get_fourcc_code(self.output_format))
        video_writer = cv2.VideoWriter(
            filepath,
            fourcc,
            fps,
            (width, height),
            isColor=True
        )
        
        # 验证视频写入器是否成功创建
        if not video_writer.isOpened():
            print(f"错误：无法创建视频写入器，路径: {filepath}")
            return None
            
        return video_writer
    
    def _get_fourcc_code(self, output_format):
        """根据输出格式返回合适的FourCC编码"""
        format_map = {
            "mp4": "H264",  # 使用H264编码器，更兼容Windows
            "avi": "XVID",
            "mov": "MJPG"
        }
        
        # 尝试获取主要编码器，如果失败则尝试备选编码器
        primary_codec = format_map.get(output_format.lower(), "H264")
        try:
            # 尝试创建主要编码器
            fourcc = cv2.VideoWriter_fourcc(*primary_codec)
            return primary_codec
        except Exception as e:
            print(f"警告：主要编码器 {primary_codec} 创建失败，尝试备选编码器")
            # 备选编码器映射
            fallback_map = {
                "H264": ["avc1", "X264", "mp4v"],
                "XVID": ["DIVX", "mp4v"],
                "MJPG": ["mp4v"]
            }
            
            # 尝试备选编码器
            for codec in fallback_map.get(primary_codec, ["mp4v"]):
                try:
                    fourcc = cv2.VideoWriter_fourcc(*codec)
                    print(f"使用备选编码器: {codec}")
                    return codec
                except Exception:
                    continue
            
            # 如果所有编码器都失败，返回最基本的编码器
            print("所有编码器尝试失败，使用基本编码器 'mp4v'")
            return "mp4v"

    def stop_recording(self):
        if not self.recording:
            return False
            
        if self.video_writer:
            # 计算实际录制时长和帧率
            elapsed_time = time.time() - self.start_time
            actual_fps = self.frame_count / elapsed_time if elapsed_time > 0 else 0
            print(f"录制完成：时长 {elapsed_time:.2f} 秒，总帧数 {self.frame_count}，实际帧率 {actual_fps:.2f}")
            
            self.video_writer.release()
            self.video_writer = None
            
        self.recording = False
        self.frame_count = 0
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
            try:
                if not self.video_writer.write(frame):
                    print(f"警告：帧写入失败，当前帧计数：{self.frame_count}")
                else:
                    self.frame_count += 1
                    
                if time.time() - self.last_record_time >= self.interval:
                    if self._rotate_video_file(frame):
                        self.last_record_time = time.time()
            except Exception as e:
                print(f"错误：视频写入异常 - {str(e)}")
                self.stop_recording()

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