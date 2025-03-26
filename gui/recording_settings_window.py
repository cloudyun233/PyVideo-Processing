# gui/recording_settings_window.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QLineEdit, QPushButton, QSpinBox,
                             QFormLayout, QGroupBox)
from PyQt5.QtCore import Qt

class RecordingSettingsWindow(QWidget):
    """视频录制设置窗口"""
    
    def __init__(self, video_recorder, parent=None):
        super().__init__(parent)
        self.video_recorder = video_recorder
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("视频录制设置")
        self.setWindowFlags(Qt.Window)
        self.resize(400, 300)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # 录制设置组
        settings_group = QGroupBox("录制设置")
        settings_layout = QFormLayout()
        
        # 文件格式选择
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4", "AVI"])
        settings_layout.addRow("视频格式:", self.format_combo)
        
        # 存储间隔设置
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 120)  # 1-120分钟
        self.interval_spin.setValue(1)
        self.interval_spin.setSuffix(" 分钟")
        settings_layout.addRow("存储间隔:", self.interval_spin)
        
        # 文件前缀设置
        self.prefix_edit = QLineEdit("video")
        settings_layout.addRow("文件前缀:", self.prefix_edit)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("保存设置")
        self.save_btn.clicked.connect(self.save_settings)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.close)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(button_layout)
        
        # 加载当前设置
        self.load_current_settings()
        # 连接视频录制器的状态变化信号
        self.video_recorder.recording_state_changed.connect(self.update_ui_state)
        
    def load_current_settings(self):
        """加载当前设置"""
        # 这里可以添加从video_recorder加载当前设置的逻辑
        # 暂时使用默认值
        pass

    def update_ui_state(self, is_recording):
        """更新UI状态"""
        self.setEnabled(not is_recording)
        if is_recording:
            QMessageBox.information(self, "提示", "正在录制中，无法更改设置")
        
    def save_settings(self):
        """保存设置"""
        # 获取设置值
        file_format = self.format_combo.currentText().lower()
        interval = self.interval_spin.value() * 60  # 转换为秒
        file_prefix = self.prefix_edit.text().strip()
        
        # 更新video_recorder的设置
        if hasattr(self.video_recorder, 'output_format'):
            self.video_recorder.output_format = file_format
        if hasattr(self.video_recorder, 'interval'):
            self.video_recorder.interval = interval
        if hasattr(self.video_recorder, 'file_prefix'):
            self.video_recorder.file_prefix = file_prefix or "video"
        
        # 通知父窗口设置已更新
        if self.parent:
            self.parent.statusBar().showMessage("录制设置已保存", 3000)
            
        self.close()