# gui/video_playback_window.py
import os
import cv2
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QSlider, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from video_playback import VideoPlayback

class VideoPlaybackWindow(QWidget):
    """视频回放窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.playback = VideoPlayback()
        self.video_analyzer = parent.video_analyzer  # 获取父窗口的视频分析器
        self.analyzed_frame = None
        self.dual_view = False
        self.timer = QTimer(self)
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("视频回放")
        self.resize(800, 600)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 视频选择区域
        self.select_button = QPushButton("选择视频文件")
        self.file_label = QLabel("未选择文件")
        self.file_label.setWordWrap(True)
        
        # 视频显示区域
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("background-color: black;")
        
        # 控制按钮区域
        self.play_button = QPushButton("播放")
        self.pause_button = QPushButton("暂停")
        self.stop_button = QPushButton("停止")
        
        # 进度条
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.setEnabled(False)
        
        # 状态标签
        self.status_label = QLabel("状态: 等待选择视频文件")
        
        # 布局设置
        control_layout = QHBoxLayout()
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.stop_button)
        
        main_layout.addWidget(self.select_button)
        main_layout.addWidget(self.file_label)
        main_layout.addWidget(self.video_label)
        main_layout.addWidget(self.progress_slider)
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.status_label)
        
    def setup_connections(self):
        """设置信号和槽连接"""
        self.select_button.clicked.connect(self.select_video)
        self.play_button.clicked.connect(self.play_video)
        self.pause_button.clicked.connect(self.pause_video)
        self.stop_button.clicked.connect(self.stop_video)
        self.progress_slider.sliderMoved.connect(self.seek_video)
        self.timer.timeout.connect(self.update_frame)
        
        # 设置视频回放回调
        self.playback.set_callbacks(
            status_callback=self.update_status,
            end_callback=self.on_playback_end
        )
        
    def select_video(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", 
            "视频文件 (*.mp4 *.avi *.mov *.mkv);;所有文件 (*.*)"
        )
        
        if file_path:
            self.file_label.setText(file_path)
            if self.playback.open_video(file_path):
                self.progress_slider.setEnabled(True)
                self.progress_slider.setRange(0, self.playback.get_duration())
                self.update_status(f"状态: 已加载视频 {os.path.basename(file_path)}")
            else:
                self.update_status("状态: 无法加载视频")
                
    def play_video(self):
        """播放视频"""
        if self.playback.play():
            self.timer.start(30)  # 约30ms更新一次
            self.update_status("状态: 播放中")
            
    def pause_video(self):
        """暂停视频"""
        if self.playback.pause():
            self.timer.stop()
            self.update_status("状态: 已暂停")
            
    def stop_video(self):
        """停止视频"""
        self.playback.stop()
        self.timer.stop()
        self.video_label.clear()
        self.video_label.setText("视频已停止")
        self.progress_slider.setValue(0)
        
    def seek_video(self, position):
        """跳转到指定位置"""
        if self.playback.seek(position):
            frame = self.playback.get_frame()
            if frame is not None:
                self.display_frame(frame)
                
    def update_frame(self):
        """更新视频帧"""
        if self.playback.is_playing():
            frame = self.playback.get_frame()
            if frame is not None:
                # 如果启用了分析且是回放分析
                if self.video_analyzer.analyzing and hasattr(self, 'playback_analysis') and self.playback_analysis:
                    self.analyzed_frame = self.video_analyzer.analyze_frame(frame)
                    
                # 双窗口显示
                if self.dual_view and self.analyzed_frame is not None:
                    self.display_dual_view(frame, self.analyzed_frame)
                else:
                    # 单窗口显示
                    display_frame = self.analyzed_frame if (self.analyzed_frame is not None and 
                                                          self.video_analyzer.analyzing) else frame
                    self.display_single_view(display_frame)
                    
                self.progress_slider.setValue(self.playback.get_position())
            else:
                self.on_playback_end()
                
    def display_frame(self, frame):
        """显示视频帧"""
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(q_img).scaled(
            self.video_label.width(), self.video_label.height(),
            Qt.KeepAspectRatio
        ))
        
    def update_status(self, message):
        """更新状态信息"""
        self.status_label.setText(message)
        
    def on_playback_end(self):
        """播放结束处理"""
        self.timer.stop()
        self.update_status("状态: 播放完成")
        self.playback.stop()
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.playback.stop()
        self.timer.stop()
        event.accept()