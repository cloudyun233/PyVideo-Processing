# gui/main_window.py
import sys
import os
from .video_processing_window import VideoProcessingWindow
from .camera_preview_window import CameraPreviewWindow
from .recording_settings_window import RecordingSettingsWindow
from .video_playback_window import VideoPlaybackWindow
from .video_analysis_settings_window import VideoAnalysisSettingsWindow
from video_recorder import VideoRecorder
from .video_playback_window import VideoPlaybackWindow
from .video_analysis_settings_window import VideoAnalysisSettingsWindow
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QComboBox, 
                             QVBoxLayout, QHBoxLayout, QWidget, QLabel, QGroupBox, 
                             QGridLayout, QSizePolicy, QSpacerItem)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

# 导入视频工具类

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from video_utils import VideoUtils
from video_analyzer import VideoAnalyzer


class MainWindow(QMainWindow):
    """视频处理系统主窗口"""
    
    def __init__(self):
        super().__init__()
        self.utils = VideoUtils()
        self.video_recorder = VideoRecorder()
        self.video_analyzer = VideoAnalyzer()  # 添加视频分析器
        self.preview_window = None
        self.settings_window = None
        self.processing_window = None
        self.analysis_settings_window = None  # 分析设置窗口
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和大小
        self.setWindowTitle("视频处理系统")
        self.resize(800, 600)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 创建顶部控制区域
        top_control_group = QGroupBox("控制面板")
        top_control_layout = QGridLayout(top_control_group)
        
        # 创建摄像头选择区域
        camera_label = QLabel("选择摄像头:")
        camera_label.setFont(QFont("Arial", 10))
        self.camera_combo = QComboBox()
        self.camera_combo.setMinimumWidth(150)
        self.camera_combo.setFont(QFont("Arial", 10))
        
        # 获取可用摄像头列表
        camera_list = self.utils.detect_cameras()
        if camera_list:
            self.camera_combo.addItems(camera_list)
        else:
            self.camera_combo.addItem("未检测到摄像头")
        
        # 创建按钮
        self.open_camera_btn = self.create_button("打开摄像头", "启动摄像头预览")
        self.record_settings_btn = self.create_button("视频录制设置", "配置视频录制参数")
        self.video_process_btn = self.create_button("本地视频格式处理", "处理本地视频文件格式")
        self.video_playback_btn = self.create_button("本地视频回放", "播放本地视频文件")
        self.video_analysis_btn = self.create_button("视频智能分析设置", "配置视频智能分析参数")
        
        # 添加控件到布局
        top_control_layout.addWidget(camera_label, 0, 0)
        top_control_layout.addWidget(self.camera_combo, 0, 1)
        top_control_layout.addWidget(self.open_camera_btn, 0, 2)
        top_control_layout.addWidget(self.record_settings_btn, 1, 0)
        top_control_layout.addWidget(self.video_process_btn, 1, 1)
        top_control_layout.addWidget(self.video_playback_btn, 1, 2)
        top_control_layout.addWidget(self.video_analysis_btn, 2, 0, 1, 3)
        
        # 添加到主布局
        main_layout.addWidget(top_control_group)
        
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
        
        # 连接按钮信号
        self.connect_signals()
        
    def create_button(self, text, tooltip):
        """创建统一样式的按钮"""
        button = QPushButton(text)
        button.setToolTip(tooltip)
        button.setMinimumHeight(40)
        button.setFont(QFont("Arial", 10))
        return button
    
    def connect_signals(self):
        """连接信号和槽"""
        self.open_camera_btn.clicked.connect(self.on_open_camera)
        self.record_settings_btn.clicked.connect(self.on_record_settings)
        self.video_process_btn.clicked.connect(self.on_video_process)
        self.video_playback_btn.clicked.connect(self.on_video_playback)
        self.video_analysis_btn.clicked.connect(self.on_video_analysis)
    
    def on_open_camera(self):
        """打开摄像头按钮点击事件"""
        if self.preview_window is not None:
            self.statusBar().showMessage("摄像头预览窗口已打开")
            return
            
        camera_index = self.camera_combo.currentText()
        if not camera_index or camera_index == "未检测到摄像头":
            self.statusBar().showMessage("请选择有效的摄像头")
            return
        # 创建预览窗口并传递视频分析器
        self.preview_window = CameraPreviewWindow(camera_index, self.video_recorder, self.video_analyzer)
        self.preview_window.closed.connect(self.on_preview_closed)
        self.preview_window.show()
        self.statusBar().showMessage(f"已打开摄像头 {camera_index}")

    def on_preview_closed(self):
        """预览窗口关闭时的处理"""
        self.preview_window = None
        self.statusBar().showMessage("摄像头已关闭")
    
    def on_record_settings(self):
        """视频录制设置按钮点击事件"""
        if not hasattr(self, 'settings_window') or not self.settings_window:
            self.settings_window = RecordingSettingsWindow(self.video_recorder, self)
            self.settings_window.show()
        else:
            self.settings_window.show()
            self.settings_window.raise_()
    
    def on_video_process(self):
        """本地视频格式处理按钮点击事件"""
        if not hasattr(self, 'processing_window') or not self.processing_window:
            self.processing_window = VideoProcessingWindow(self)
            self.processing_window.show()
        else:
            self.processing_window.show()
            self.processing_window.raise_()
    
    def on_video_playback(self):
        """本地视频回放按钮点击事件"""
        if not hasattr(self, 'playback_window') or not self.playback_window:
            self.playback_window = VideoPlaybackWindow(self)
            self.playback_window.show()
        else:
            self.playback_window.show()
            self.playback_window.raise_()
    
    def on_video_analysis(self):
        """视频智能分析设置按钮点击事件"""
        if not hasattr(self, 'analysis_settings_window') or not self.analysis_settings_window:
            self.analysis_settings_window = VideoAnalysisSettingsWindow(self.video_analyzer, self)
            self.analysis_settings_window.settings_changed.connect(self.handle_analysis_settings)
            self.analysis_settings_window.show()
        else:
            self.analysis_settings_window.show()
            self.analysis_settings_window.raise_()
    def handle_analysis_settings(self, settings):
        """处理分析设置变化"""
        self.statusBar().showMessage(f"视频分析设置已更新: {settings}")