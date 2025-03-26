# gui/main_window.py

import os
import sys
import cv2
import time
import threading
from datetime import datetime

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QHBoxLayout, QCheckBox, QSlider,
    QMainWindow, QWidget, QPushButton, QComboBox, QHBoxLayout, QVBoxLayout,
    QLabel, QDialog, QFileDialog, QLineEdit, QProgressBar, QMessageBox, QCheckBox,
    QListWidget, QListWidgetItem, QGroupBox, QFormLayout, QSpinBox, QApplication
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QImage, QPixmap

# 导入后台处理模块
from video_recorder import VideoRecorder
from video_processor import VideoProcessor
from video_analyzer import VideoAnalyzer
from video_playback import VideoPlayback
from video_utils import VideoUtils

###########################################################
# 辅助函数：将OpenCV图像转换为QPixmap
###########################################################
def cvFrame_to_qpixmap(frame, target_size=None):
    if frame is None:
        return QPixmap()
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    h, w, ch = rgb_frame.shape
    bytes_per_line = ch * w
    image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
    pixmap = QPixmap.fromImage(image)
    if target_size:
        pixmap = pixmap.scaled(target_size, Qt.KeepAspectRatio)
    return pixmap

###########################################################
# 主窗口
###########################################################
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频处理系统")
        self.setGeometry(100, 100, 400, 300)
        self._init_ui()

    def _init_ui(self):
        widget = QWidget()
        layout = QVBoxLayout()
      
        # 摄像头选择下拉框（使用video_recorder检测摄像头）
        self.recorder = VideoRecorder()
        camera_list = self.recorder.get_camera_list()
        self.camera_combo = QComboBox()
        if camera_list:
            self.camera_combo.addItems(camera_list)
        else:
            self.camera_combo.addItem("0")
        layout.addWidget(QLabel("选择摄像头"))
        layout.addWidget(self.camera_combo)
      
        # 五个功能按钮
        self.btn_open_camera = QPushButton("打开摄像头")
        self.btn_video_record_setting = QPushButton("视频录制设置")
        self.btn_local_video_format = QPushButton("本地视频格式处理")
        self.btn_local_video_playback = QPushButton("本地视频回放")
        self.btn_video_analyze_setting = QPushButton("视频智能分析设置")
      
        layout.addWidget(self.btn_open_camera)
        layout.addWidget(self.btn_video_record_setting)
        layout.addWidget(self.btn_local_video_format)
        layout.addWidget(self.btn_local_video_playback)
        layout.addWidget(self.btn_video_analyze_setting)
      
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # 连接信号
        self.btn_open_camera.clicked.connect(self.open_camera_window)
        self.btn_video_record_setting.clicked.connect(self.open_video_record_settings)
        self.btn_local_video_format.clicked.connect(self.open_local_video_format)
        self.btn_local_video_playback.clicked.connect(self.open_local_video_playback)
        self.btn_video_analyze_setting.clicked.connect(self.open_video_analyze_settings)

    def open_camera_window(self):
        cam_index = self.camera_combo.currentText()
        self.camera_window = OpenCameraDialog(camera_index=cam_index, recorder=self.recorder)
        self.camera_window.show()
  
    def open_video_record_settings(self):
        # 弹出视频录制设置窗口
        self.record_setting_dialog = VideoRecordSettingsDialog(recorder=self.recorder)
        self.record_setting_dialog.exec_()
  
    def open_local_video_format(self):
        # 弹出本地视频格式处理窗口
        self.local_video_format_dialog = LocalVideoFormatProcessingDialog()
        self.local_video_format_dialog.exec_()
  
    def open_local_video_playback(self):
        # 弹出本地视频回放窗口
        self.video_playback_dialog = LocalVideoPlaybackDialog()
        self.video_playback_dialog.exec_()
  
    def open_video_analyze_settings(self):
        # 弹出视频智能分析设置窗口
        self.video_analyze_setting_dialog = VideoAnalyzeSettingsDialog()
        self.video_analyze_setting_dialog.exec_()

###########################################################
# 打开摄像头窗口
###########################################################
class OpenCameraDialog(QDialog):
    def __init__(self, camera_index, recorder: VideoRecorder):
        super().__init__()
        self.setWindowTitle("摄像头预览及实时检测")
        self.recorder = recorder
        self.camera_index = int(camera_index)
        self.resize(800, 600)
      
        # 后端视频分析器（实时检测）
        self.analyzer = VideoAnalyzer()
        # 默认无模型，如需车辆/行人则需要提前加载模型（此处在使用时需调用加载模型界面）
      
        # 标记是否正在分析
        self.analysis_enabled = False
      
        self._init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)
      
        # 开始摄像头预览
        self.recorder.start_preview(camera_index=self.camera_index)
  
    def _init_ui(self):
        layout = QVBoxLayout()
      
        # 视频显示区域：使用QLabel（扩展时可替换为QGraphicsView）
        self.video_label = QLabel("视频预览")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_label, stretch=1)
      
        # 操作按钮行
        btn_layout = QHBoxLayout()
        self.btn_start_record = QPushButton("开始录制")
        self.btn_stop_record = QPushButton("停止录制")
        btn_layout.addWidget(self.btn_start_record)
        btn_layout.addWidget(self.btn_stop_record)
        layout.addLayout(btn_layout)
      
        # 检测复选框：人脸、行人、车辆
        check_layout = QHBoxLayout()
        self.check_face = QCheckBox("人脸检测")
        self.check_person = QCheckBox("行人检测")
        self.check_vehicle = QCheckBox("车辆检测")
        check_layout.addWidget(self.check_face)
        check_layout.addWidget(self.check_person)
        check_layout.addWidget(self.check_vehicle)
        layout.addLayout(check_layout)
      
        # 锁定录制、检测设置的标识（在本窗口内控制）
        self.btn_start_record.clicked.connect(self.start_recording)
        self.btn_stop_record.clicked.connect(self.stop_recording)
      
        # 每次勾选发生变化时更新分析检测类型
        self.check_face.stateChanged.connect(self.update_detection_types)
        self.check_person.stateChanged.connect(self.update_detection_types)
        self.check_vehicle.stateChanged.connect(self.update_detection_types)
      
        self.setLayout(layout)

    def update_detection_types(self):
        types = []
        if self.check_face.isChecked():
            types.append("face")
        if self.check_person.isChecked():
            types.append("person")
        if self.check_vehicle.isChecked():
            types.append("vehicle")
        self.analyzer.set_detection_types(types)
        
        # 统一控制分析器启停
        if types:
            if self.analyzer.start_analysis():
                # 当需要YOLO模型时检测加载状态
                if ("vehicle" in types or "person" in types) and not self.analyzer.yolo_model:
                    QMessageBox.warning(self, "提示", "车辆或行人检测需加载YOLO模型！\n请先在智能分析设置中加载模型。")
                    self.analyzer.stop_analysis()
        else:
            self.analyzer.stop_analysis()
  
    def start_recording(self):
        # 调用video_recorder的开始录制接口，注意录制设置必须事先在“录制设置”中配置好（例如存储间隔、格式、前缀）
        if self.recorder.start_recording():
            self.btn_start_record.setEnabled(False)
            self.btn_stop_record.setEnabled(True)
        else:
            QMessageBox.warning(self, "提示", "录制可能已启动或摄像头未就绪！")
  
    def stop_recording(self):
        if self.recorder.stop_recording():
            self.btn_stop_record.setEnabled(False)
            self.btn_start_record.setEnabled(True)
  
    def update_frame(self):
        ret, frame = self.recorder.get_frame()
        if not ret or frame is None:
            return
      
        # 如果检测选项开启且分析器已启动，则进行检测
        if len(self.analyzer.detection_types) > 0:
            frame = self.analyzer.analyze_frame(frame)
      
        pix = cvFrame_to_qpixmap(frame, target_size=self.video_label.size())
        self.video_label.setPixmap(pix)
  
    def closeEvent(self, event):
        # 关闭窗口时停止预览和录制
        self.timer.stop()
        self.recorder.stop_preview()
        event.accept()

###########################################################
# 视频录制设置对话框
###########################################################
class VideoRecordSettingsDialog(QDialog):
    def __init__(self, recorder: VideoRecorder):
        super().__init__()
        self.setWindowTitle("视频录制设置")
        self.recorder = recorder
        self.resize(400, 200)
        self._init_ui()
  
    def _init_ui(self):
        layout = QFormLayout()
      
        # 存储间隔：单位秒，示例采用60s和300s（1分钟和5分钟）
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(10, 3600)
        self.interval_spin.setValue(60)
        layout.addRow("存储间隔（秒）：", self.interval_spin)
      
        # 录制格式选择
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp4", "avi"])
        layout.addRow("录制格式：", self.format_combo)
      
        # 文件命名前缀
        self.prefix_edit = QLineEdit()
        self.prefix_edit.setText("video")
        layout.addRow("文件前缀：", self.prefix_edit)
      
        # 保存按钮
        self.btn_save = QPushButton("保存设置")
        self.btn_save.clicked.connect(self.save_settings)
        layout.addRow(self.btn_save)
      
        self.setLayout(layout)

    def save_settings(self):
        # 如果录制中则不能调整这些设置
        if self.recorder.is_recording():
            QMessageBox.warning(self, "提示", "录制开始后不能调整设置！")
            return

        # 将设置值传给video_recorder对象
        self.recorder.interval = self.interval_spin.value()
        self.recorder.output_format = self.format_combo.currentText()
        self.recorder.file_prefix = self.prefix_edit.text() if self.prefix_edit.text() else "video"
        QMessageBox.information(self, "提示", "设置已保存！")
        self.close()

class LocalVideoFormatProcessingDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("本地视频格式处理")
        self.resize(500, 300)
        self.processor = VideoProcessor()
        self._init_ui()
  
    def _init_ui(self):
        layout = QVBoxLayout()
      
        # 选择视频文件
        file_layout = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("请选择视频文件...")
        self.btn_browse = QPushButton("选择视频")
        self.btn_browse.clicked.connect(self.select_video_file)
        file_layout.addWidget(self.file_edit)
        file_layout.addWidget(self.btn_browse)
        layout.addLayout(file_layout)
      
        # 分辨率调整下拉框
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1080p", "720p", "480p"])
        layout.addWidget(QLabel("输出分辨率："))
        layout.addWidget(self.resolution_combo)
      
        # 帧率调整下拉框
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["60", "30", "15"])
        layout.addWidget(QLabel("输出帧率："))
        layout.addWidget(self.fps_combo)
      
        # 输出视频格式列表
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp4", "avi"])
        layout.addWidget(QLabel("输出视频格式："))
        layout.addWidget(self.format_combo)
      
        # 开始转换按钮和进度条
        self.btn_start = QPushButton("开始转换")
        self.btn_start.clicked.connect(self.start_conversion)
        layout.addWidget(self.btn_start)
      
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
      
        self.setLayout(layout)
  
    def select_video_file(self):
        """选择单个视频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择视频文件", 
            os.getcwd(),
            "Video Files (*.mp4 *.avi);;All Files (*)"
        )
        if file_path:
            self.file_edit.setText(file_path)
            # 设置保存路径为视频所在目录
            save_path = os.path.dirname(file_path)
            self.processor.save_path = save_path
  
    def start_conversion(self):
        file_path = self.file_edit.text().strip()
        if not file_path or not os.path.isfile(file_path):
            QMessageBox.warning(self, "提示", "请选择有效的视频文件！")
            return
      
        # 检查文件是否为支持的视频格式
        if not file_path.lower().endswith((".mp4", ".avi")):
            QMessageBox.warning(self, "提示", "请选择支持的视频格式（.mp4 或 .avi）！")
            return
      
        # 计算参数：分辨率、帧率
        res_text = self.resolution_combo.currentText()
        if res_text == "1080p":
            width, height = 1920, 1080
        elif res_text == "720p":
            width, height = 1280, 720
        elif res_text == "480p":
            width, height = 854, 480
        else:
            width, height = 1280, 720
      
        fps = int(self.fps_combo.currentText())
        output_format = self.format_combo.currentText()
      
        # 设置进度条
        self.progress_bar.setValue(0)
        
        # 设置状态回调以更新进度条
        def update_progress(status):
            if "处理中" in status:
                try:
                    percent = int(status.split()[-1].rstrip("%"))
                    self.progress_bar.setValue(percent)
                    QApplication.processEvents()
                except:
                    pass
        
        self.processor.status_callback = update_progress
        
        # 执行视频处理
        success, result = self.processor.process_video(file_path, width, height, fps, output_format)
        if not success:
            QMessageBox.warning(self, "错误", f"处理失败: {result}")
            return
            
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "提示", f"视频转换完成！\n保存至: {result}")
        self.close()

###########################################################
# 本地视频回放窗口
###########################################################
class LocalVideoPlaybackDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("本地视频回放")
        self.resize(1920, 1080)
        self.playback = VideoPlayback()
        self._init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
  
    def _init_ui(self):
        layout = QVBoxLayout()
      
        # 选择视频文件
        file_layout = QHBoxLayout()
        self.file_edit = QLineEdit()
        self.btn_browse = QPushButton("选择视频")
        self.btn_browse.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_edit)
        file_layout.addWidget(self.btn_browse)
        layout.addLayout(file_layout)
      
        self.btn_start = QPushButton("开始播放")
        self.btn_start.clicked.connect(self.start_play)
        layout.addWidget(self.btn_start)
      
        # 播放控制按钮
        ctrl_layout = QHBoxLayout()
        self.btn_pause = QPushButton("暂停/继续")
        self.btn_stop = QPushButton("停止")
        ctrl_layout.addWidget(self.btn_pause)
        ctrl_layout.addWidget(self.btn_stop)
        layout.addLayout(ctrl_layout)
      
        # 检测复选框
        check_layout = QHBoxLayout()
        self.check_face = QCheckBox("人脸检测")
        self.check_person = QCheckBox("行人检测")
        self.check_vehicle = QCheckBox("车辆检测")
        check_layout.addWidget(self.check_face)
        check_layout.addWidget(self.check_person)
        check_layout.addWidget(self.check_vehicle)
        layout.addLayout(check_layout)
      
        # 视频显示区域
        # 进度条
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.sliderMoved.connect(self.seek_video)
        layout.addWidget(self.slider)

        self.video_label = QLabel("视频回放")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_label, stretch=1)
      
        # 连接按钮
        self.btn_pause.clicked.connect(self.toggle_pause)
        self.btn_stop.clicked.connect(self.stop_play)

      
        # 初始化视频分析器（回放时也支持检测）
        self.analyzer = VideoAnalyzer()
        self.check_face.stateChanged.connect(self.update_detection_types)
        self.check_person.stateChanged.connect(self.update_detection_types)
        self.check_vehicle.stateChanged.connect(self.update_detection_types)
      
        self.setLayout(layout)
  
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择视频文件", os.getcwd(), "视频文件 (*.mp4 *.avi)")
        if file_path:
            self.file_edit.setText(file_path)
  
    def start_play(self):
        file_path = self.file_edit.text().strip()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "提示", "请选择有效的视频文件！")
            return
        if self.playback.open_video(file_path):
            self.playback.play()
            self.timer.start(30)
        else:
            QMessageBox.warning(self, "提示", "无法打开视频文件！")
  
    def update_frame(self):
        frame = self.playback.get_frame()
        if frame is None:
            self.timer.stop()
            return
        # 更新进度条
        self.slider.setMaximum(self.playback.get_duration())
        self.slider.setValue(self.playback.get_position())
        # 如果检测开启，则调用分析
        if len(self.analyzer.detection_types) > 0:
            frame = self.analyzer.analyze_frame(frame)
        pix = cvFrame_to_qpixmap(frame, target_size=self.video_label.size())
        self.video_label.setPixmap(pix)
  
    def toggle_pause(self):
        if self.playback.paused:
            self.playback.play()
            self.btn_pause.setText("暂停")
            if not self.timer.isActive():
                self.timer.start(30)
        else:
            self.playback.pause()
            self.btn_pause.setText("播放")
            self.timer.stop()
  
    def stop_play(self):
        self.playback.stop()
        self.timer.stop()
        self.video_label.clear()
  
    def fast_forward(self):
        # 快进5秒
        fps = self.playback.get_fps()
        current = self.playback.get_position()
        self.playback.seek(current + int(fps * 5))
  
    def update_detection_types(self):
        types = []
        if self.check_face.isChecked():
            types.append("face")
        if self.check_person.isChecked():
            types.append("person")
        if self.check_vehicle.isChecked():
            types.append("vehicle")
        self.analyzer.set_detection_types(types)
        if types:
            self.analyzer.start_analysis()
        else:
            self.analyzer.stop_analysis()
  
    def seek_video(self, position):
        self.playback.seek(position)

    def closeEvent(self, event):
        self.stop_play()
        event.accept()

###########################################################
# 视频智能分析设置窗口（用于加载和选择YOLO模型）
###########################################################
class VideoAnalyzeSettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频智能分析设置")
        self.resize(400, 300)
        self.analyzer = VideoAnalyzer()
        self._init_ui()
  
    def _init_ui(self):
        layout = QVBoxLayout()
      
        # 模型列表
        self.model_list = QListWidget()
        available_models = self.analyzer.get_available_models()
        if available_models:
            for model in available_models:
                item = QListWidgetItem(model)
                self.model_list.addItem(item)
        else:
            self.model_list.addItem("未检测到模型")
        layout.addWidget(QLabel("选择YOLO模型："))
        layout.addWidget(self.model_list)
      
        self.btn_load_model = QPushButton("加载选中模型")
        self.btn_load_model.clicked.connect(self.load_model)
        layout.addWidget(self.btn_load_model)
      
        self.setLayout(layout)
  
    def load_model(self):
        if self.analyzer.analyzing:
            QMessageBox.warning(self, "提示", "视频分析开始后不能更换模型！")
            return
        selected_items = self.model_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "提示", "请先选择一个模型")
            return
        model_name = selected_items[0].text()
        if self.analyzer.load_yolo_model(model_name):
            # 更新所有打开的摄像头窗口中的analyzer实例
            for window in QApplication.topLevelWidgets():
                if isinstance(window, OpenCameraDialog):
                    window.analyzer.load_yolo_model(model_name)
            QMessageBox.information(self, "提示", f"已加载模型 {model_name}")
        else:
            QMessageBox.warning(self, "提示", "加载模型失败！")
        self.close()

###########################################################
# 如有需要，还可以添加其他辅助窗口...
###########################################################