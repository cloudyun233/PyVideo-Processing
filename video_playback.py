# video_playback.py
import cv2
import os
from PyQt5.QtCore import QObject, pyqtSignal


class VideoPlayback(QObject):
    """视频回放类，负责视频文件的播放、暂停和控制"""

    def __init__(self):
        """初始化视频回放对象"""
        super().__init__()
        self.cap = None  # 视频捕获对象
        self.paused = False  # 暂停状态标志
        self.current_file = None  # 当前视频文件路径
        self.frame_callback = None  # 帧回调函数
        self.status_callback = None  # 状态回调函数
        self.end_callback = None  # 结束回调函数

    def set_callbacks(self, frame_callback=None, status_callback=None, end_callback=None):
        """设置帧、状态和结束的回调函数

        Args:
            frame_callback (callable, optional): 帧处理回调函数
            status_callback (callable, optional): 状态更新回调函数
            end_callback (callable, optional): 视频结束回调函数
        """
        self.frame_callback = frame_callback
        self.status_callback = status_callback
        self.end_callback = end_callback

    def open_video(self, file_path):
        """打开指定路径的视频文件

        Args:
            file_path (str): 视频文件路径

        Returns:
            bool: 打开是否成功
        """
        if not os.path.exists(file_path):
            if self.status_callback:
                self.status_callback("状态：视频文件不存在")
            return False

        self.close_video()  # 关闭已有视频
        self.cap = cv2.VideoCapture(file_path)
        if not self.cap.isOpened():
            if self.status_callback:
                self.status_callback("状态：无法打开视频文件")
            return False

        self.current_file = file_path
        self.paused = False
        if self.status_callback:
            self.status_callback("状态：视频已加载")
        return True

    def close_video(self):
        """关闭当前打开的视频"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            self.current_file = None
            self.paused = False

    def play(self):
        """开始播放视频

        Returns:
            bool: 播放是否成功
        """
        if self.cap is not None and self.cap.isOpened():
            self.paused = False
            if self.status_callback:
                self.status_callback("状态：播放中")
            return True
        return False

    def pause(self):
        """暂停视频播放

        Returns:
            bool: 暂停是否成功
        """
        if self.cap is not None and self.cap.isOpened():
            self.paused = True
            if self.status_callback:
                self.status_callback("状态：已暂停")
            return True
        return False

    def stop(self):
        """停止播放并关闭视频"""
        end_callback = self.end_callback  # 保存回调引用
        self.end_callback = None  # 防止递归调用
        self.close_video()
        if self.status_callback:
            self.status_callback("状态：已停止")
        if end_callback:
            end_callback()

    def seek(self, position):
        """跳转到指定帧位置

        Args:
            position (int): 目标帧位置

        Returns:
            bool: 跳转是否成功
        """
        if self.cap is not None and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, position)
            return True
        return False

    def get_frame(self):
        """获取当前视频帧

        Returns:
            numpy.ndarray or None: 当前帧图像，失败时返回 None
        """
        if self.cap is None or not self.cap.isOpened() or self.paused:
            return None

        ret, frame = self.cap.read()
        if not ret:
            if self.end_callback:
                self.end_callback()
            return None
        return frame

    def get_position(self):
        """获取当前播放帧位置

        Returns:
            int: 当前帧号，失败时返回 0
        """
        if self.cap is not None and self.cap.isOpened():
            return int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        return 0

    def get_duration(self):
        """获取视频总帧数

        Returns:
            int: 总帧数，失败时返回 0
        """
        if self.cap is not None and self.cap.isOpened():
            return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        return 0

    def get_fps(self):
        """获取视频帧率

        Returns:
            float: 帧率，失败时返回 0
        """
        if self.cap is not None and self.cap.isOpened():
            return self.cap.get(cv2.CAP_PROP_FPS)
        return 0

    def is_playing(self):
        """检查视频是否正在播放

        Returns:
            bool: 是否正在播放
        """
        return self.cap is not None and self.cap.isOpened() and not self.paused