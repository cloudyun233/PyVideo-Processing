# gui/video_analysis_settings.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal

class VideoAnalysisSettings(QWidget):
    """视频智能分析设置窗口"""
    
    settings_changed = pyqtSignal(dict)  # 设置改变信号
    
    def __init__(self, video_analyzer, parent=None):
        super().__init__(parent, Qt.Window)
        self.video_analyzer = video_analyzer
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("视频智能分析设置")
        self.resize(400, 200)  # 减小高度
        
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # YOLO模型选择组
        model_group = QGroupBox("模型选择")
        model_layout = QVBoxLayout(model_group)
        
        self.model_combo = QComboBox()
        available_models = self.video_analyzer.get_available_models()
        if available_models:
            self.model_combo.addItems(available_models)
        else:
            self.model_combo.addItem("未找到可用模型")
        
        model_layout.addWidget(QLabel("选择YOLO模型:"))
        model_layout.addWidget(self.model_combo)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.apply_btn = QPushButton("应用")
        self.cancel_btn = QPushButton("取消")
        
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.cancel_btn)
        
        # 添加到主布局
        main_layout.addWidget(model_group)
        main_layout.addLayout(button_layout)
        
        # 连接信号
        self.apply_btn.clicked.connect(self.apply_settings)
        self.cancel_btn.clicked.connect(self.close)
    
    def apply_settings(self):
        """应用设置"""
        # 加载选中的YOLO模型
        model_name = self.model_combo.currentText()
        if model_name != "未找到可用模型":
            self.video_analyzer.load_yolo_model(model_name)
        
        # 发送设置改变信号
        settings = {
            'model': model_name,
            'detections': []  # 不再处理检测类型
        }
        self.settings_changed.emit(settings)
        self.close()
