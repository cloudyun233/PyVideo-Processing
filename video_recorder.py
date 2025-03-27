import os
import time
from datetime import datetime
import cv2
from PyQt5.QtCore import QObject, pyqtSignal
from video_utils import VideoUtils


class VideoRecorder(QObject):
    """视频录制类，用于摄像头预览和视频录制"""
    recording_state_changed = pyqtSignal(bool)

    def __init__(self):
        """初始化视频录制器"""
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
        self.interval = 30  # 默认分段间隔30秒
        self.file_prefix = "video"
        self.frame_count = 0
        self.start_time = 0

    def set_callbacks(self, frame_callback=None, status_callback=None):
        """设置帧回调和状态回调函数"""
        self.frame_callback = frame_callback
        self.status_callback = status_callback

    def get_camera_list(self):
        """获取可用摄像头列表"""
        return self.utils.detect_cameras()

    def set_save_path(self, path):
        """设置视频保存路径"""
        if os.path.isdir(path):
            self.save_path = path
            return True
        return False

    def get_max_camera_resolution(self, camera_index):
        """获取指定摄像头最大分辨率"""
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            return 1280, 720  # 默认分辨率
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return width, height

    def start_preview(self, camera_index, width=None, height=None, fps=None):
        """启动摄像头预览"""
        if self.previewing:
            return True

        try:
            camera_index = int(camera_index)
        except ValueError:
            self._update_status("请选择有效摄像头")
            return False

        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self._update_status("无法启动摄像头")
            return False

        # 未指定分辨率时使用默认值
        if width is None or height is None:
            width, height = self.get_max_camera_resolution(camera_index)

        # 设置摄像头参数，逐步降级尝试
        resolutions = [(width, height), (1280, 720), (640, 480)]
        for w, h in resolutions:
            if self._set_camera_params(w, h, fps):
                self.previewing = True
                self._update_status("预览中")
                return True
        self._release_camera()
        self._update_status("无法设置任何分辨率")
        return False

    def _set_camera_params(self, width, height, fps):
        """设置摄像头参数"""
        success = (self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width) and
                   self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height))
        if fps is not None:
            success &= self.cap.set(cv2.CAP_PROP_FPS, fps)
        return success

    def stop_preview(self):
        """停止摄像头预览"""
        if self.recording:
            self.stop_recording()
        self.previewing = False
        self._release_camera()
        self._update_status("就绪")

    def _release_camera(self):
        """释放摄像头资源"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def start_recording(self, output_format=None, interval=None):
        """开始录制视频"""
        if not self.cap or self.recording:
            return False

        self.interval = int(interval) if interval is not None else self.interval
        self.output_format = output_format or self.output_format
        self.video_writer = self._create_writer()

        if self.video_writer is None:
            self._update_status("无法创建视频写入器")
            return False

        self.recording = True
        self.recording_state_changed.emit(True)
        self.start_time = time.time()
        self.last_record_time = self.start_time
        self.frame_count = 0
        self._update_status("录制中")
        return True

    def _create_writer(self):
        """创建视频写入器"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.file_prefix}_{timestamp}.{self.output_format}"
        filepath = os.path.join(self.save_path, filename)
        os.makedirs(self.save_path, exist_ok=True)

        fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*self._get_fourcc_code(self.output_format))
        writer = cv2.VideoWriter(filepath, fourcc, fps, (width, height), isColor=True)

        if not writer.isOpened():
            print(f"错误：无法创建视频写入器，路径: {filepath}")
            return None
        return writer

    def _get_fourcc_code(self, output_format):
        """根据输出格式获取FourCC编码"""
        format_map = {
            "mp4": "mp4v",  # 更兼容的编码
            "avi": "XVID",
            "mov": "MJPG"
        }
        return format_map.get(output_format.lower(), "mp4v")

    def stop_recording(self):
        """停止录制视频"""
        if not self.recording:
            return False

        if self.video_writer is not None:
            elapsed_time = time.time() - self.start_time
            actual_fps = self.frame_count / elapsed_time if elapsed_time > 0 else 0
            self.video_writer.release()
            self.video_writer = None
            self._update_status(f"录制完成：时长 {elapsed_time:.2f} 秒，总帧数 {self.frame_count}")

        self.recording = False
        self.frame_count = 0
        self.recording_state_changed.emit(False)
        self._update_status("预览中")
        return True

    def get_frame(self):
        """获取当前帧"""
        if not self.previewing or not self.cap:
            return False, None

        ret, frame = self.cap.read()
        if not ret:
            self._update_status("无法读取帧")
            return False, None

        if self.recording:
            self._write_frame(frame)
        return True, frame

    def _write_frame(self, frame):
        """写入视频帧并处理分段"""
        try:
            self.video_writer.write(frame)
            self.frame_count += 1

            current_time = time.time()
            if current_time - self.last_record_time >= self.interval:
                self._rotate_video_file(frame)
                self.last_record_time = current_time
        except Exception as e:
            self._update_status(f"视频写入失败: {str(e)}")
            self.stop_recording()

    def _rotate_video_file(self, frame):
        """分段轮换视频文件"""
        try:
            if self.video_writer is not None:
                self.video_writer.release()

            self.video_writer = self._create_writer()
            if self.video_writer is None:
                self._update_status("无法创建新视频文件")
                return

            self.video_writer.write(frame)
            self._update_status(f"已创建新视频文件，总帧数 {self.frame_count}")
        except Exception as e:
            self._update_status(f"视频轮换失败: {str(e)}")
            if self.video_writer is not None:
                self.video_writer.release()
                self.video_writer = None

    def _update_status(self, message):
        """更新状态信息"""
        if self.status_callback is not None:
            self.status_callback(f"状态：{message}")

    def is_previewing(self):
        """检查是否正在预览"""
        return self.previewing

    def is_recording(self):
        """检查是否正在录制"""
        return self.recording