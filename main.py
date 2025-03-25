import sys
import os
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QComboBox, QLineEdit, QFileDialog, 
                             QCheckBox, QSlider, QTabWidget, QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap

# 导入自定义模块
from video_processor import VideoProcessor
from video_playback import VideoPlayback
from video_recorder import VideoRecorder
from video_utils import VideoUtils


class VideoStreamApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频流处理应用")
        self.setGeometry(100, 100, 1200, 800)

        # 初始化组件
        self.video_processor = VideoProcessor()
        self.video_playback = VideoPlayback()
        self.video_recorder = VideoRecorder()
        self.utils = VideoUtils()
        
        # 设置保存路径
        self.save_path = os.getcwd()
        
        # 定时器用于视频更新
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        
        # 设置回调函数
        self.video_processor.set_status_callback(self.update_status)
        self.video_playback.set_callbacks(
            frame_callback=self.display_playback_frame,
            status_callback=self.update_status,
            end_callback=self.on_playback_end
        )
        self.video_recorder.set_callbacks(
            frame_callback=self.display_camera_frame,
            status_callback=self.update_status
        )
        
        # 初始化UI
        self.init_ui()

    def init_ui(self):
        # 主窗口设置
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # 左侧控制面板
        control_widget = QWidget()
        control_widget.setFixedWidth(300)
        control_layout = QVBoxLayout(control_widget)

        # 使用选项卡组织功能
        tab_widget = QTabWidget()
        
        # 摄像头标签页
        camera_tab = QWidget()
        camera_layout = QVBoxLayout(camera_tab)
        self.init_camera_tab(camera_layout)
        tab_widget.addTab(camera_tab, "摄像头")
        
        # 回放标签页
        playback_tab = QWidget()
        playback_layout = QVBoxLayout(playback_tab)
        self.init_playback_tab(playback_layout)
        tab_widget.addTab(playback_tab, "视频回放")
        
        # 处理标签页
        process_tab = QWidget()
        process_layout = QVBoxLayout(process_tab)
        self.init_process_tab(process_layout)
        tab_widget.addTab(process_tab, "视频处理")
        
        control_layout.addWidget(tab_widget)
        
        # 状态显示
        self.status_label = QLabel("状态：就绪")
        control_layout.addWidget(self.status_label)
        
        main_layout.addWidget(control_widget)

        # 右侧视频预览窗口
        self.video_widget = QWidget()
        self.video_layout = QVBoxLayout(self.video_widget)
        
        # 视频显示标签
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(800, 600)
        self.video_label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.video_layout.addWidget(self.video_label)

        # 播放控制
        self.playback_controls = QWidget()
        self.playback_layout = QHBoxLayout(self.playback_controls)
        self.play_btn = QPushButton("播放", clicked=self.play_video)
        self.pause_btn = QPushButton("暂停", clicked=self.pause_video)
        self.stop_playback_btn = QPushButton("停止", clicked=self.stop_playback)
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.sliderMoved.connect(self.seek_video)
        self.playback_layout.addWidget(self.play_btn)
        self.playback_layout.addWidget(self.pause_btn)
        self.playback_layout.addWidget(self.stop_playback_btn)
        self.playback_layout.addWidget(self.seek_slider)
        self.video_layout.addWidget(self.playback_controls)
        self.playback_controls.hide()
        
        main_layout.addWidget(self.video_widget)

    def init_camera_tab(self, layout):
        # 摄像头设置组
        camera_group = QGroupBox("摄像头设置")
        camera_layout = QVBoxLayout()
        
        # 摄像头选择
        self.camera_label = QLabel("选择摄像头：")
        self.camera_combo = QComboBox()
        self.camera_combo.addItems(self.video_recorder.get_camera_list())
        camera_layout.addWidget(self.camera_label)
        camera_layout.addWidget(self.camera_combo)
        
        # 分辨率选择
        self.resolution_label = QLabel("选择分辨率：")
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["640x480", "1280x720", "1920x1080"])
        self.resolution_combo.setCurrentText("640x480")
        camera_layout.addWidget(self.resolution_label)
        camera_layout.addWidget(self.resolution_combo)
        
        # 帧率选择
        self.fps_label = QLabel("选择帧率：")
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["15", "30", "60"])
        self.fps_combo.setCurrentText("30")
        camera_layout.addWidget(self.fps_label)
        camera_layout.addWidget(self.fps_combo)
        
        camera_group.setLayout(camera_layout)
        layout.addWidget(camera_group)
        
        # 录制设置组
        record_group = QGroupBox("录制设置")
        record_layout = QVBoxLayout()
        
        # 录制间隔
        self.interval_label = QLabel("录制间隔（秒）：")
        self.interval_edit = QLineEdit("60")
        record_layout.addWidget(self.interval_label)
        record_layout.addWidget(self.interval_edit)
        
        # 保存路径
        self.path_label = QLabel("保存路径：")
        self.path_edit = QLineEdit(self.save_path)
        self.path_button = QPushButton("选择路径", clicked=self.select_path)
        record_layout.addWidget(self.path_label)
        record_layout.addWidget(self.path_edit)
        record_layout.addWidget(self.path_button)
        
        # 文件格式
        self.convert_check = QCheckBox("转换为AVI")
        record_layout.addWidget(self.convert_check)
        
        record_group.setLayout(record_layout)
        layout.addWidget(record_group)
        
        # 控制按钮
        self.start_preview_btn = QPushButton("开始预览", clicked=self.start_preview)
        self.stop_preview_btn = QPushButton("停止预览", clicked=self.stop_preview)
        self.start_record_btn = QPushButton("开始录制", clicked=self.start_recording)
        self.stop_record_btn = QPushButton("停止录制", clicked=self.stop_recording)
        
        # 初始状态设置
        self.stop_preview_btn.setEnabled(False)
        self.start_record_btn.setEnabled(False)
        self.stop_record_btn.setEnabled(False)
        
        layout.addWidget(self.start_preview_btn)
        layout.addWidget(self.stop_preview_btn)
        layout.addWidget(self.start_record_btn)
        layout.addWidget(self.stop_record_btn)

    def init_playback_tab(self, layout):
        # 视频选择组
        playback_group = QGroupBox("视频回放")
        playback_layout = QVBoxLayout()
        
        # 选择视频文件
        self.playback_file_label = QLabel("视频文件：")
        self.playback_file_edit = QLineEdit()
        self.playback_file_btn = QPushButton("选择文件", clicked=self.select_playback_file)
        playback_layout.addWidget(self.playback_file_label)
        playback_layout.addWidget(self.playback_file_edit)
        playback_layout.addWidget(self.playback_file_btn)
        
        # 播放按钮
        self.playback_btn = QPushButton("播放视频", clicked=self.playback_video)
        playback_layout.addWidget(self.playback_btn)
        
        playback_group.setLayout(playback_layout)
        layout.addWidget(playback_group)
        layout.addStretch()

    def init_process_tab(self, layout):
        # 视频处理组
        process_group = QGroupBox("视频处理")
        process_layout = QVBoxLayout()
        
        # 选择视频文件
        self.process_file_label = QLabel("视频文件：")
        self.process_file_edit = QLineEdit()
        self.process_file_btn = QPushButton("选择文件", clicked=self.select_process_file)
        process_layout.addWidget(self.process_file_label)
        process_layout.addWidget(self.process_file_edit)
        process_layout.addWidget(self.process_file_btn)
        
        # 处理选项
        self.process_resolution_label = QLabel("输出分辨率：")
        self.process_resolution_combo = QComboBox()
        self.process_resolution_combo.addItems(["640x480", "1280x720", "1920x1080"])
        
        self.process_fps_label = QLabel("输出帧率：")
        self.process_fps_combo = QComboBox()
        self.process_fps_combo.addItems(["15", "30", "60"])
        
        self.process_format_check = QCheckBox("转换为AVI")
        
        process_layout.addWidget(self.process_resolution_label)
        process_layout.addWidget(self.process_resolution_combo)
        process_layout.addWidget(self.process_fps_label)
        process_layout.addWidget(self.process_fps_combo)
        process_layout.addWidget(self.process_format_check)
        
        # 处理按钮
        self.process_btn = QPushButton("开始处理", clicked=self.process_video)
        process_layout.addWidget(self.process_btn)
        
        # 帧提取选项
        self.extract_interval_label = QLabel("提取间隔（秒）：")
        self.extract_interval_edit = QLineEdit("1")
        self.extract_btn = QPushButton("提取帧", clicked=self.extract_frames)
        
        process_layout.addWidget(self.extract_interval_label)
        process_layout.addWidget(self.extract_interval_edit)
        process_layout.addWidget(self.extract_btn)
        
        process_group.setLayout(process_layout)
        layout.addWidget(process_group)
        layout.addStretch()

    def update_status(self, status_text):
        """更新状态栏文本"""
        self.status_label.setText(status_text)

    def select_path(self):
        """选择保存路径"""
        path = QFileDialog.getExistingDirectory(self, "选择保存路径")
        if path:
            self.save_path = path
            self.path_edit.setText(path)
            self.video_recorder.set_save_path(path)
            self.video_processor.set_save_path(path)

    def start_preview(self):
        """开始摄像头预览"""
        try:
            camera_index = self.camera_combo.currentText()
            width, height = map(int, self.resolution_combo.currentText().split('x'))
            fps = int(self.fps_combo.currentText())
            
            if self.video_recorder.start_preview(camera_index, width, height, fps):
                self.start_preview_btn.setEnabled(False)
                self.stop_preview_btn.setEnabled(True)
                self.start_record_btn.setEnabled(True)
                self.timer.start(1000 // fps)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"启动预览失败: {str(e)}")

    def stop_preview(self):
        """停止摄像头预览"""
        self.video_recorder.stop_preview()
        self.timer.stop()
        self.video_label.clear()
        self.start_preview_btn.setEnabled(True)
        self.stop_preview_btn.setEnabled(False)
        self.start_record_btn.setEnabled(False)
        self.stop_record_btn.setEnabled(False)

    def start_recording(self):
        """开始录制视频"""
        try:
            # 设置录制间隔
            self.video_recorder.interval = int(self.interval_edit.text())
            
            # 设置输出格式
            output_format = "avi" if self.convert_check.isChecked() else "mp4"
            
            if self.video_recorder.start_recording(output_format):
                self.start_record_btn.setEnabled(False)
                self.stop_record_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"开始录制失败: {str(e)}")

    def stop_recording(self):
        """停止录制视频"""
        self.video_recorder.stop_recording()
        self.start_record_btn.setEnabled(True)
        self.stop_record_btn.setEnabled(False)

    def update_frame(self):
        """定时更新视频帧"""
        # 如果正在预览摄像头
        if self.video_recorder.is_previewing():
            ret, frame = self.video_recorder.get_frame()
            if ret:
                self.display_camera_frame(frame)
        # 如果正在播放视频
        elif self.video_playback.is_playing():
            frame = self.video_playback.get_frame()
            if frame is not None:
                self.display_playback_frame(frame)
                # 更新进度条
                self.seek_slider.setValue(self.video_playback.get_position())

    def display_camera_frame(self, frame):
        """显示摄像头帧"""
        pixmap = self.utils.convert_frame_to_pixmap(frame, self.video_label.size())
        if pixmap:
            self.video_label.setPixmap(pixmap)

    def display_playback_frame(self, frame):
        """显示回放帧"""
        pixmap = self.utils.convert_frame_to_pixmap(frame, self.video_label.size())
        if pixmap:
            self.video_label.setPixmap(pixmap)

    def select_playback_file(self):
        """选择要播放的视频文件"""
        file_path = QFileDialog.getOpenFileName(self, "选择视频文件", "", "视频文件 (*.mp4 *.avi)")
        if file_path and file_path[0]:
            self.playback_file_edit.setText(file_path[0])

    def playback_video(self):
        """播放视频文件"""
        file_path = self.playback_file_edit.text()
        if not file_path:
            QMessageBox.warning(self, "警告", "请先选择视频文件")
            return
            
        # 如果正在预览，先停止预览
        if self.video_recorder.is_previewing():
            self.stop_preview()
            
        # 打开视频文件
        if self.video_playback.open_video(file_path):
            # 设置进度条范围
            self.seek_slider.setRange(0, self.video_playback.get_duration())
            
            # 开始播放
            self.video_playback.play()
            
            # 显示播放控制
            self.playback_controls.show()
            
            # 启动定时器，使用视频实际帧率
            fps = self.video_playback.get_fps()
            if fps > 0:
                self.timer.start(int(1000 / fps))
            else:
                self.timer.start(33)  # 默认约30fps

    def play_video(self):
        """继续播放视频"""
        self.video_playback.play()

    def pause_video(self):
        """暂停视频播放"""
        self.video_playback.pause()

    def stop_playback(self):
        """停止视频播放"""
        self.timer.stop()
        self.video_playback.stop()
        self.video_label.clear()
        self.playback_controls.hide()

    def seek_video(self, position):
        """视频快进/后退"""
        self.video_playback.seek(position)

    def on_playback_end(self):
        """视频播放结束回调"""
        self.stop_playback()

    def select_process_file(self):
        """选择要处理的视频文件"""
        file_path = QFileDialog.getOpenFileName(self, "选择视频文件", "", "视频文件 (*.mp4 *.avi)")
        if file_path and file_path[0]:
            self.process_file_edit.setText(file_path[0])

    def process_video(self):
        """处理视频文件"""
        input_file = self.process_file_edit.text()
        if not input_file:
            QMessageBox.warning(self, "警告", "请先选择视频文件")
            return
            
        try:
            # 获取处理参数
            width, height = map(int, self.process_resolution_combo.currentText().split('x'))
            fps = float(self.process_fps_combo.currentText())
            output_format = "avi" if self.process_format_check.isChecked() else "mp4"
            
            # 处理视频
            success, result = self.video_processor.process_video(input_file, width, height, fps, output_format)
            
            if success:
                QMessageBox.information(self, "成功", f"视频处理完成，已保存至:\n{result}")
            else:
                QMessageBox.warning(self, "失败", f"视频处理失败: {result}")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"处理视频时发生错误: {str(e)}")

    def extract_frames(self):
        """从视频中提取帧"""
        input_file = self.process_file_edit.text()
        if not input_file:
            QMessageBox.warning(self, "警告", "请先选择视频文件")
            return
            
        try:
            # 获取提取间隔
            interval = float(self.extract_interval_edit.text())
            
            # 创建输出目录
            video_name = os.path.splitext(os.path.basename(input_file))[0]
            output_dir = os.path.join(self.save_path, f"{video_name}_frames")
            
            # 提取帧
            success, count = self.video_processor.extract_frames(input_file, output_dir, interval)
            
            if success:
                QMessageBox.information(self, "成功", f"已提取 {count} 帧，保存至:\n{output_dir}")
            else:
                QMessageBox.warning(self, "失败", "帧提取失败")
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"提取帧时发生错误: {str(e)}")

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止预览和播放
        self.stop_preview()
        self.stop_playback()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoStreamApp()
    window.show()
    sys.exit(app.exec_())