# gui/video_processing_window.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QFileDialog, QGroupBox,
                             QFormLayout, QProgressBar)
from PyQt5.QtCore import Qt
import os
from video_processor import VideoProcessor

class VideoProcessingWindow(QWidget):
    """视频处理窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.video_processor = VideoProcessor()
        self.input_file = ""
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("本地视频格式处理")
        self.setWindowFlags(Qt.Window)
        self.resize(500, 400)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # 文件选择区域
        file_group = QGroupBox("视频文件")
        file_layout = QHBoxLayout()
        
        self.file_label = QLabel("未选择文件")
        self.file_label.setWordWrap(True)
        
        self.select_file_btn = QPushButton("选择文件")
        self.select_file_btn.clicked.connect(self.select_video_file)
        
        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(self.select_file_btn)
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # 处理设置区域
        settings_group = QGroupBox("处理设置")
        settings_layout = QFormLayout()
        
        # 分辨率选择
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            "1080p (1920x1080)",
            "720p (1280x720)",
            "480p (854x480)"
        ])
        settings_layout.addRow("输出分辨率:", self.resolution_combo)
        
        # 帧率选择
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["60 FPS", "45 FPS", "30 FPS", "15 FPS"])
        settings_layout.addRow("输出帧率:", self.fps_combo)
        
        # 格式选择
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4", "AVI", "保持原格式"])
        settings_layout.addRow("输出格式:", self.format_combo)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.process_btn = QPushButton("开始转换")
        self.process_btn.setEnabled(False)
        self.process_btn.clicked.connect(self.process_video)
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(self.process_btn)
        button_layout.addWidget(self.close_btn)
        main_layout.addLayout(button_layout)
        
        # 设置状态回调
        self.video_processor.set_status_callback(self.update_status)
        
    def select_video_file(self):
        """选择视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频文件", "", 
            "视频文件 (*.mp4 *.avi *.mov *.mkv);;所有文件 (*.*)"
        )
        
        if file_path:
            self.input_file = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.process_btn.setEnabled(True)
            
            # 更新状态
            if self.parent:
                self.parent.statusBar().showMessage(f"已选择文件: {file_path}", 3000)
    
    def process_video(self):
        """处理视频"""
        if not self.input_file or not os.path.exists(self.input_file):
            self.update_status("状态：请选择有效视频文件")
            return
            
        # 获取设置
        resolution = self.resolution_combo.currentText()
        fps_text = self.fps_combo.currentText()
        output_format = self.format_combo.currentText()
        
        # 解析分辨率
        if resolution.startswith("1080p"):
            width, height = 1920, 1080
        elif resolution.startswith("720p"):
            width, height = 1280, 720
        elif resolution.startswith("480p"):
            width, height = 854, 480
        else:
            # 自定义分辨率 - 这里可以添加自定义分辨率对话框
            width, height = 1280, 720  # 默认使用720p
            
        # 解析帧率
        fps = int(fps_text.split()[0])
        
        # 解析输出格式
        if output_format == "保持原格式":
            # 获取原始文件扩展名
            ext = os.path.splitext(self.input_file)[1][1:].lower()
            output_format = ext if ext in ["mp4", "avi"] else "mp4"
        else:
            output_format = output_format.lower()
            
        # 重置进度条
        self.progress_bar.setValue(0)
        
        # 开始处理
        success, result = self.video_processor.process_video(
            self.input_file,
            width=width,
            height=height,
            fps=fps,
            output_format=output_format
        )
        
        if success:
            self.progress_bar.setValue(100)
            self.update_status(f"状态：处理完成，文件已保存到 {result}")
        else:
            self.update_status(f"状态：处理失败 - {result}")
    
    def update_status(self, message):
        """更新状态"""
        if message.startswith("状态：处理中"):
            # 提取进度百分比
            if "%" in message:
                try:
                    percent = int(message.split(" ")[-1].replace("%", ""))
                    self.progress_bar.setValue(percent)
                except:
                    pass
                    
        if self.parent:
            self.parent.statusBar().showMessage(message, 3000)
    
    def closeEvent(self, event):
        """关闭窗口事件"""
        if self.parent:
            self.parent.statusBar().showMessage("就绪")
        super().closeEvent(event)