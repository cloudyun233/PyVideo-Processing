# video_recorder.py
import cv2
import os
import time
from datetime import datetime
from PyQt5.QtCore import QObject
from video_utils import VideoUtils


class VideoRecorder(QObject):
    """视频录制类，负责摄像头视频流的捕获、预览和录制"""
    
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
        self.output_format = "mp4"  # 默认输出格式
        self.interval = 60  # 默认60秒
        self.file_prefix = "video"  # 默认文件前缀
        
    def set_callbacks(self, frame_callback=None, status_callback=None):
        """设置回调函数"""
        self.frame_callback = frame_callback
        self.status_callback = status_callback
        
    def get_camera_list(self):
        """获取可用摄像头列表"""
        return self.utils.detect_cameras()
        
    def set_save_path(self, path):
        """设置保存路径"""
        if os.path.exists(path) and os.path.isdir(path):
            self.save_path = path
            return True
        return False
    
    def get_max_camera_resolution(self, camera_index):
        """获取摄像头支持的最大分辨率
        
        Args:
            camera_index: 摄像头索引
        
        Returns:
            tuple: (最大宽度, 最大高度)
        """
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            return (640, 480)
        
        # 获取支持的最大分辨率
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        return (width, height)

    def get_max_camera_fps(self, camera_index):
        """获取摄像头支持的最大帧率
        
        Args:
            camera_index: 摄像头索引
        
        Returns:
            float: 最大帧率
        """
        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            return 30.0
        
        # 获取支持的最大帧率
        fps = cap.get(cv2.CAP_PROP_FPS)
        cap.release()
        return fps

    def start_preview(self, camera_index, width=None, height=None, fps=None):
        """开始摄像头预览
        
        Args:
            camera_index: 摄像头索引
            width: 视频宽度，如果为None则使用最大分辨率
            height: 视频高度，如果为None则使用最大分辨率
            fps: 帧率，如果为None则使用最大帧率
            
        Returns:
            bool: 是否成功启动预览
        """
        if self.previewing:
            return True
            
        try:
            # 尝试将camera_index转换为整数
            camera_index = int(camera_index)
        except ValueError:
            if self.status_callback:
                self.status_callback("状态：请选择有效摄像头")
            return False
            
        # 获取最大分辨率和帧率
        if width is None or height is None:
            width, height = self.get_max_camera_resolution(camera_index)
        if fps is None:
            fps = self.get_max_camera_fps(camera_index)
        
        # 打开摄像头
        self.cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        
        if not self.cap.isOpened():
            if self.status_callback:
                self.status_callback("状态：无法打开摄像头")
            return False
            
        self.previewing = True
        
        if self.status_callback:
            self.status_callback("状态：预览中")
            
        return True
    
    def stop_preview(self):
        """停止摄像头预览"""
        # 如果正在录制，先停止录制
        if self.recording:
            self.stop_recording()
            
        self.previewing = False
        
        # 释放资源
        if self.cap:
            self.cap.release()
            self.cap = None
            
        if self.status_callback:
            self.status_callback("状态：就绪")
    
    def start_recording(self, output_format=None, interval=None):
        """开始录制视频
        
        Args:
            output_format: 输出格式 (mp4 或 avi)，如果为None则使用当前设置
            interval: 定时保存间隔（秒），如果为None则使用当前设置
        """
        if self.recording or not self.cap or not self.cap.isOpened():
            return False
            
        self.recording = True
        self.last_record_time = time.time()
        
        # 使用参数或当前设置
        output_format = output_format if output_format is not None else self.output_format
        self.interval = interval if interval is not None else self.interval
        
        # 初始化视频写入器
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = output_format.lower()
        filename = os.path.join(self.save_path, f"{self.file_prefix}_{timestamp}.{ext}")
        
        # 获取适当的fourcc编码
        fourcc = self.utils.get_fourcc(ext)
        
        # 获取摄像头实际分辨率和帧率
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        # 创建视频写入器
        self.video_writer = cv2.VideoWriter(filename, fourcc, fps, (width, height), isColor=True)
        
        if self.status_callback:
            self.status_callback("状态：录制中")
            
        return True
    
    def stop_recording(self):
        """停止录制视频"""
        if not self.recording:
            return False
            
        self.recording = False
        
        # 释放视频写入器
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            
        if self.status_callback:
            self.status_callback("状态：预览中")
            
        return True
    
    def save_new_video_file(self, frame, output_format=None):
        """定时保存新视频文件
        
        Args:
            frame: 当前视频帧
            output_format: 输出格式 (mp4 或 avi)，如果为None则使用当前设置
        """
        if not self.recording or not self.cap or not self.cap.isOpened():
            return False
            
        # 使用参数或当前设置
        output_format = output_format if output_format is not None else self.output_format
        
        # 释放当前写入器
        if self.video_writer:
            self.video_writer.release()
            
        # 创建新文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = output_format.lower()
        filename = os.path.join(self.save_path, f"{self.file_prefix}_{timestamp}.{ext}")
        
        # 获取适当的fourcc编码
        fourcc = self.utils.get_fourcc(ext)
        
        # 获取摄像头实际分辨率和帧率
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        # 创建新的视频写入器
        self.video_writer = cv2.VideoWriter(filename, fourcc, fps, (width, height), isColor=True)
        
        # 写入当前帧
        self.video_writer.write(frame)
        
        # 更新时间戳
        self.last_record_time = time.time()
        
        return True
    
    def get_frame(self):
        """获取当前摄像头帧
        
        Returns:
            tuple: (是否成功, 帧数据)
        """
        if not self.previewing or not self.cap or not self.cap.isOpened():
            return False, None
            
        ret, frame = self.cap.read()
        if not ret:
            return False, None
            
        # 如果正在录制，写入帧
        if self.recording and self.video_writer:
            self.video_writer.write(frame)
            
            # 检查是否需要定时保存新文件
            current_time = time.time()
            try:
                interval = int(self.interval)
            except (AttributeError, ValueError):
                interval = 60  # 默认60秒
                
            if current_time - self.last_record_time >= interval:
                self.save_new_video_file(frame)
        
        # 返回BGR格式的帧
        return True, frame
    
    def is_previewing(self):
        """检查是否正在预览"""
        return self.previewing
    
    def is_recording(self):
        """检查是否正在录制"""
        return self.recording