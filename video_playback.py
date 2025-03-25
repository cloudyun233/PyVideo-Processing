import cv2
import os
from PyQt5.QtCore import QObject, pyqtSignal


class VideoPlayback(QObject):
    """视频回放类，负责视频文件的播放、暂停和控制"""
    
    def __init__(self):
        super().__init__()
        self.cap = None
        self.paused = False
        self.current_file = None
        self.frame_callback = None
        self.status_callback = None
        self.end_callback = None
        
    def set_callbacks(self, frame_callback=None, status_callback=None, end_callback=None):
        """设置回调函数"""
        self.frame_callback = frame_callback
        self.status_callback = status_callback
        self.end_callback = end_callback
        
    def open_video(self, file_path):
        """打开视频文件"""
        if not os.path.exists(file_path):
            if self.status_callback:
                self.status_callback("状态：视频文件不存在")
            return False
            
        # 如果已经有打开的视频，先关闭
        self.close_video()
        
        # 打开新视频
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
        """关闭当前视频"""
        if self.cap:
            self.cap.release()
            self.cap = None
            self.current_file = None
            self.paused = False
    
    def play(self):
        """播放视频"""
        if self.cap and self.cap.isOpened():
            self.paused = False
            if self.status_callback:
                self.status_callback("状态：播放中")
            return True
        return False
    
    def pause(self):
        """暂停视频"""
        if self.cap and self.cap.isOpened():
            self.paused = True
            if self.status_callback:
                self.status_callback("状态：已暂停")
            return True
        return False
    
    def stop(self):
        """停止播放并关闭视频"""
        # 保存end_callback的引用，因为close_video会将其设为None
        callback = self.end_callback
        # 先将end_callback设为None，防止递归调用
        self.end_callback = None
        
        self.close_video()
        if self.status_callback:
            self.status_callback("状态：已停止")
        # 如果有回调，在最后调用它
        if callback:
            callback()
    
    def seek(self, position):
        """跳转到指定位置"""
        if self.cap and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, position)
            return True
        return False
    
    def get_frame(self):
        """获取当前帧"""
        if not self.cap or not self.cap.isOpened() or self.paused:
            return None
            
        ret, frame = self.cap.read()
        if not ret:
            # 视频结束
            if self.end_callback:
                self.end_callback()
            return None
            
        return frame
    
    def get_position(self):
        """获取当前播放位置"""
        if self.cap and self.cap.isOpened():
            return int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        return 0
    
    def get_duration(self):
        """获取视频总帧数"""
        if self.cap and self.cap.isOpened():
            return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        return 0
    
    def get_fps(self):
        """获取视频帧率"""
        if self.cap and self.cap.isOpened():
            return self.cap.get(cv2.CAP_PROP_FPS)
        return 0
    
    def is_playing(self):
        """检查是否正在播放"""
        return self.cap is not None and self.cap.isOpened() and not self.paused