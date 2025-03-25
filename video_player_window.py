import cv2
import os
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QSlider, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QCloseEvent
from video_utils import VideoUtils


class VideoPlayerWindow(QMainWindow):
    """视频播放窗口类，负责视频显示和播放控制"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("视频播放窗口")
        self.setGeometry(200, 200, 800, 600)
        
        # 初始化组件
        self.utils = VideoUtils()
        
        # 初始化UI
        self.init_ui()
        
        # 关闭事件处理
        self.closeEvent = self.handle_close_event
        
        # 父窗口引用
        self.parent_window = parent
        
    def init_ui(self):
        # 主窗口设置
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # 视频显示区域
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.video_label)
        
        # 播放控制区域
        self.playback_controls = QWidget()
        self.playback_layout = QHBoxLayout(self.playback_controls)
        
        # 播放控制按钮
        self.play_btn = QPushButton("播放")
        self.pause_btn = QPushButton("暂停")
        self.stop_btn = QPushButton("停止")
        
        # 进度条
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setMinimum(0)
        self.seek_slider.setMaximum(100)  # 默认值，将在播放时更新
        
        # 添加到布局
        self.playback_layout.addWidget(self.play_btn)
        self.playback_layout.addWidget(self.pause_btn)
        self.playback_layout.addWidget(self.stop_btn)
        self.playback_layout.addWidget(self.seek_slider)
        
        main_layout.addWidget(self.playback_controls)
    
    def set_button_callbacks(self, play_callback, pause_callback, stop_callback, seek_callback):
        """设置按钮回调函数"""
        self.play_btn.clicked.connect(play_callback)
        self.pause_btn.clicked.connect(pause_callback)
        self.stop_btn.clicked.connect(stop_callback)
        self.seek_slider.sliderMoved.connect(seek_callback)
    
    def display_frame(self, frame):
        """显示视频帧"""
        if frame is not None:
            pixmap = self.utils.convert_frame_to_pixmap(frame, self.video_label.size())
            if pixmap:
                self.video_label.setPixmap(pixmap)
    
    def set_slider_range(self, minimum, maximum):
        """设置进度条范围"""
        self.seek_slider.setMinimum(minimum)
        self.seek_slider.setMaximum(maximum)
    
    def set_slider_value(self, value):
        """设置进度条值"""
        self.seek_slider.setValue(value)
    
    def handle_close_event(self, event: QCloseEvent):
        """处理窗口关闭事件"""
        # 通知父窗口播放窗口已关闭
        if self.parent_window and hasattr(self.parent_window, 'on_player_window_closed'):
            self.parent_window.on_player_window_closed()
        event.accept()