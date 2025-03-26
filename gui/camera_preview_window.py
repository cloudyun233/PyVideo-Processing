# gui/camera_preview_window.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QHBoxLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
import cv2

class CameraPreviewWindow(QWidget):
    """摄像头预览窗口"""
    
    closed = pyqtSignal()  # 窗口关闭信号
    
    def __init__(self, camera_index, video_recorder, video_analyzer):
        super().__init__()
        self.camera_index = camera_index
        self.video_recorder = video_recorder
        self.video_analyzer = video_analyzer
        self.analyzed_frame = None
        self.dual_view = False
        self.init_ui()
        self.init_camera()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle(f"摄像头预览 - 设备 {self.camera_index}")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.resize(800, 600)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 预览标签
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview_label.setMinimumSize(640, 480)
        main_layout.addWidget(self.preview_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.record_btn = QPushButton("开始录制")
        self.record_btn.setFixedHeight(40)
        self.record_btn.clicked.connect(self.toggle_recording)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.setFixedHeight(40)
        self.close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(self.record_btn)
        button_layout.addWidget(self.close_btn)
        main_layout.addLayout(button_layout)
        
        # 定时器用于更新画面
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # 约30fps
        
    def init_camera(self):
        """初始化摄像头"""
        if not self.video_recorder.start_preview(self.camera_index):
            self.close()
            return
            
        # 设置帧回调
        self.video_recorder.set_callbacks(
            frame_callback=self.handle_frame,
            status_callback=self.update_status
        )
        
    def toggle_recording(self):
        """切换录制状态"""
        if self.video_recorder.is_recording():
            self.video_recorder.stop_recording()
            self.record_btn.setText("开始录制")
        else:
            if self.video_recorder.start_recording():
                self.record_btn.setText("停止录制")
                
    def update_frame(self):
        """更新帧画面"""
        if not self.video_recorder.is_previewing():
            return
            
        ret, frame = self.video_recorder.get_frame()
        if ret:
            # 如果启用了分析且是实时分析
            if self.video_analyzer.analyzing and hasattr(self, 'realtime_analysis') and self.realtime_analysis:
                self.analyzed_frame = self.video_analyzer.analyze_frame(frame)
                
            # 双窗口显示
            if self.dual_view and self.analyzed_frame is not None:
                self.display_dual_view(frame, self.analyzed_frame)
            else:
                # 单窗口显示
                display_frame = self.analyzed_frame if (self.analyzed_frame is not None and 
                                                      self.video_analyzer.analyzing) else frame
                self.display_single_view(display_frame)
        
    def display_single_view(self, frame):
        """显示单窗口视图"""
        h, w = frame.shape[:2]
        bytes_per_line = 3 * w
        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        
        scaled_pixmap = pixmap.scaled(
            self.preview_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled_pixmap)

    def display_dual_view(self, original_frame, analyzed_frame):
        """显示双窗口视图"""
        # 将两个帧水平拼接
        combined_frame = cv2.hconcat([original_frame, analyzed_frame])
        
        h, w = combined_frame.shape[:2]
        bytes_per_line = 3 * w
        q_img = QImage(combined_frame.data, w, h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        
        scaled_pixmap = pixmap.scaled(
            self.preview_label.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled_pixmap)
            
    def handle_frame(self, frame):
        """处理帧数据"""
        pass  # 目前不需要额外处理
        
    def update_status(self, status):
        """更新状态"""
        self.setWindowTitle(f"摄像头预览 - 设备 {self.camera_index} ({status})")
        
    def closeEvent(self, event):
        """关闭窗口事件"""
        self.video_recorder.stop_preview()
        self.timer.stop()
        self.closed.emit()
        super().closeEvent(event)