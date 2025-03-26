# video_utils.py
import cv2
import os
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt


class VideoUtils:
    """提供视频处理的通用工具函数"""
    
    @staticmethod
    def detect_cameras(max_index=10):
        """检测可用摄像头"""
        available = []
        for i in range(max_index):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                available.append(str(i))
                cap.release()
        return available
    
    @staticmethod
    def convert_frame_to_pixmap(frame, label_size=None):
        """将OpenCV帧转换为QPixmap用于显示"""
        if frame is None:
            return None
            
        # 确保帧是RGB格式
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            if frame.dtype.name == 'uint8':
                # 检查是否需要BGR到RGB转换
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                rgb_frame = frame
        else:
            # 如果不是3通道彩色图像，转换为RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        
        # 创建QImage
        h, w = rgb_frame.shape[:2]
        qimg = QImage(rgb_frame.data, w, h, w * 3, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        
        # 如果提供了标签大小，则缩放图像
        if label_size:
            pixmap = pixmap.scaled(label_size, Qt.KeepAspectRatio)
            
        return pixmap
    
    @staticmethod
    def get_video_info(video_path):
        """获取视频文件的基本信息"""
        if not os.path.exists(video_path):
            return None
            
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
            
        info = {
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)) if cap.get(cv2.CAP_PROP_FPS) > 0 else 0
        }
        
        cap.release()
        return info
    
    @staticmethod
    def get_fourcc(file_format):
        """根据文件格式获取适当的fourcc编码"""
        try:
            if file_format.lower() == 'avi':
                return cv2.VideoWriter_fourcc(*'XVID')
            elif file_format.lower() == 'mp4':
                # 尝试使用H264编码器（更兼容Windows）
                try:
                    return cv2.VideoWriter_fourcc(*'H264')
                except Exception:
                    # 如果H264不可用，尝试其他常用编码器
                    for codec in ['avc1', 'X264', 'mp4v']:
                        try:
                            return cv2.VideoWriter_fourcc(*codec)
                        except Exception:
                            continue
                    # 如果所有尝试都失败，返回基本编码器
                    return cv2.VideoWriter_fourcc(*'mp4v')
            else:
                # 默认使用mp4编码
                return cv2.VideoWriter_fourcc(*'mp4v')
        except Exception as e:
            print(f"警告：编码器创建失败 - {str(e)}，使用基本编码器")
            return cv2.VideoWriter_fourcc(*'mp4v')