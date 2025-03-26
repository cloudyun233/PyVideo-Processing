# gui/video_analysis_settings_window.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QComboBox, QCheckBox, QGroupBox, 
                             QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal

class VideoAnalysisSettingsWindow(QWidget):
    """视频智能分析设置窗口"""
    
    settings_changed = pyqtSignal(dict)  # 设置改变信号
    
    def __init__(self, video_analyzer, parent=None):
        super().__init__(parent, Qt.Window)
        self.video_analyzer = video_analyzer
        self.setWindowTitle("视频智能分析设置")
        self.resize(500, 400)
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        main_layout = QVBoxLayout(self)
        
        # 模型选择组
        model_group = QGroupBox("模型设置")
        model_layout = QVBoxLayout()
        
        self.model_combo = QComboBox()
        available_models = self.video_analyzer.get_available_models()
        if available_models:
            self.model_combo.addItems(available_models)
        else:
            self.model_combo.addItem("无可用模型")
            self.model_combo.setEnabled(False)
            
        model_layout.addWidget(QLabel("选择分析模型:"))
        model_layout.addWidget(self.model_combo)
        model_group.setLayout(model_layout)
        
        # 检测选项组
        detection_group = QGroupBox("检测选项")
        detection_layout = QVBoxLayout()
        
        self.face_cb = QCheckBox("检测人脸")
        self.person_cb = QCheckBox("检测行人")
        self.vehicle_cb = QCheckBox("检测车辆")
        self.realtime_cb = QCheckBox("实时视频分析")
        self.playback_cb = QCheckBox("回放视频分析")
        self.dual_view_cb = QCheckBox("双窗口对比")
        
        detection_layout.addWidget(self.face_cb)
        detection_layout.addWidget(self.person_cb)
        detection_layout.addWidget(self.vehicle_cb)
        detection_layout.addWidget(self.realtime_cb)
        detection_layout.addWidget(self.playback_cb)
        detection_layout.addWidget(self.dual_view_cb)
        detection_group.setLayout(detection_layout)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        self.apply_btn = QPushButton("应用设置")
        self.cancel_btn = QPushButton("取消")
        
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.cancel_btn)
        
        # 添加到主布局
        main_layout.addWidget(model_group)
        main_layout.addWidget(detection_group)
        main_layout.addLayout(button_layout)
        
        # 连接信号
        self.apply_btn.clicked.connect(self.apply_settings)
        self.cancel_btn.clicked.connect(self.close)
        
    def apply_settings(self):
        """应用设置"""
        if self.video_analyzer.analyzing:
            QMessageBox.warning(self, "警告", "视频分析正在进行中，无法更改模型")
            return
        if not self.video_analyzer:
            QMessageBox.warning(self, "错误", "视频分析器未初始化")
            return
            
        # 获取当前设置
        settings = {
            'model': self.model_combo.currentText(),
            'face': self.face_cb.isChecked(),
            'person': self.person_cb.isChecked(),
            'vehicle': self.vehicle_cb.isChecked(),
            'realtime': self.realtime_cb.isChecked(),
            'playback': self.playback_cb.isChecked(),
            'dual_view': self.dual_view_cb.isChecked()
        }
        
        # 加载模型
        if settings['model'] != "无可用模型" and (settings['person'] or settings['vehicle']):
            if not self.video_analyzer.load_yolo_model(settings['model']):
                QMessageBox.warning(self, "错误", "模型加载失败")
                return
                
        # 设置检测类型
        detection_types = []
        if settings['face']:
            detection_types.append('face')
        if settings['person']:
            detection_types.append('person')
        if settings['vehicle']:
            detection_types.append('vehicle')
            
        self.video_analyzer.set_detection_types(detection_types)
        
        # 发送设置改变信号
        self.settings_changed.emit(settings)
        self.close()