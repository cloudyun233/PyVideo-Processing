# video_utils.py
import cv2
import os
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt


class VideoUtils:
    """提供视频处理的通用工具函数"""

    @staticmethod
    def detect_cameras(max_index=10):
        """
        检测可用摄像头

        Args:
            max_index (int): 检测的最大摄像头索引，默认值为10

        Returns:
            list: 可用摄像头索引的字符串列表
        """
        available = []
        for i in range(max_index):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                available.append(str(i))
                cap.release()
        return available

    @staticmethod
    def convert_frame_to_pixmap(frame, label_size=None):
        """
        将OpenCV帧转换为QPixmap用于显示

        Args:
            frame: OpenCV视频帧
            label_size (tuple, optional): 目标标签尺寸(宽，高)

        Returns:
            QPixmap: 转换后的像素图，或None如果输入无效
        """
        if frame is None:
            return None

        # 转换为RGB格式
        rgb_frame = (cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if len(frame.shape) == 3 and 
                     frame.shape[2] == 3 and frame.dtype.name == 'uint8'
                     else cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB))

        # 创建QImage
        height, width = rgb_frame.shape[:2]
        qimg = QImage(rgb_frame.tobytes(), width, height, width * 3, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)

        # 根据需要缩放图像
        if label_size:
            pixmap = pixmap.scaled(label_size, Qt.KeepAspectRatio)

        return pixmap

    @staticmethod
    def get_video_info(video_path):
        """
        获取视频文件的基本信息

        Args:
            video_path (str): 视频文件路径

        Returns:
            dict: 包含视频信息的字典，或None如果文件无效
        """
        if not os.path.exists(video_path):
            return None

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            cap.release()
            return None

        fps = cap.get(cv2.CAP_PROP_FPS)
        info = {
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': fps,
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps) if fps > 0 else 0
        }

        cap.release()
        return info

    @staticmethod
    def get_fourcc(file_format):
        """
        根据文件格式获取适当的FourCC编码，使用高兼容性编码器

        Args:
            file_format (str): 文件格式（如'avi', 'mp4'）

        Returns:
            int: FourCC编码值
        """
        file_format = file_format.lower()
        if file_format == 'avi':
            return cv2.VideoWriter_fourcc(*'XVID')
        # 对于mp4或其他格式，使用mp4v作为高兼容性默认编码器
        return cv2.VideoWriter_fourcc(*'mp4v')