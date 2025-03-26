# video_processor.py
import cv2
import os
from datetime import datetime
from PyQt5.QtCore import QObject


class VideoProcessor(QObject):
    """视频处理类，负责视频格式转换、分辨率调整等处理功能"""
    
    def __init__(self):
        super().__init__()
        self.status_callback = None
        self.save_path = os.getcwd()
        
    def set_status_callback(self, callback):
        """设置状态回调函数"""
        self.status_callback = callback
        
    def set_save_path(self, path):
        """设置保存路径"""
        if os.path.exists(path) and os.path.isdir(path):
            self.save_path = path
            return True
        return False
    
    def process_video(self, input_file, width, height, fps, output_format="mp4"):
        """处理视频文件
        
        Args:
            input_file: 输入视频文件路径
            width: 目标宽度
            height: 目标高度
            fps: 目标帧率
            output_format: 输出格式 (mp4 或 avi)
            
        Returns:
            bool: 处理是否成功
            str: 输出文件路径或错误信息
        """
        # 注意：此方法会保持视频时长不变，即使改变了帧率
        # 检查输入文件
        if not input_file or not os.path.exists(input_file):
            if self.status_callback:
                self.status_callback("状态：请选择有效视频文件")
            return False, "输入文件不存在"

        # 打开视频文件
        cap = cv2.VideoCapture(input_file)
        if not cap.isOpened():
            if self.status_callback:
                self.status_callback("状态：无法打开视频文件")
            return False, "无法打开视频文件"

        try:
            # 设置输出格式和编码器
            ext = output_format.lower()
            if ext not in ["mp4", "avi"]:
                ext = "mp4"  # 默认使用mp4
                
            fourcc = cv2.VideoWriter_fourcc(*'XVID') if ext == "avi" else cv2.VideoWriter_fourcc(*'mp4v')
            
            # 创建输出文件名
            # 获取原文件名（不带扩展名）
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.save_path, f"{base_name}_{timestamp}.{ext}")
            
            # 获取原始视频信息
            original_fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 计算原始视频时长（秒）
            original_duration = total_frames / original_fps if original_fps > 0 else 0
            
            # 创建视频写入器，使用目标帧率
            out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
            
            # 处理每一帧
            frame_count = 0
            
            # 如果原始帧率和目标帧率不同，需要调整帧的选取
            if original_fps > 0 and fps > 0 and abs(original_fps - fps) > 0.1:
                # 计算帧采样率，确保输出视频时长与原视频相同
                # 如果目标帧率高于原始帧率，可能需要重复某些帧
                # 如果目标帧率低于原始帧率，需要跳过某些帧
                frame_ratio = original_fps / fps
                target_total_frames = int(total_frames / frame_ratio)
                
                while cap.isOpened():
                    # 计算当前应该读取的帧位置
                    target_frame_pos = int(frame_count * frame_ratio)
                    
                    # 设置读取位置
                    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame_pos)
                    
                    ret, frame = cap.read()
                    if not ret:
                        break
                        
                    # 调整帧大小
                    resized_frame = cv2.resize(frame, (width, height))
                    out.write(resized_frame)
                    
                    # 更新进度
                    frame_count += 1
                    if self.status_callback and frame_count % 30 == 0:  # 每30帧更新一次状态
                        progress = int((frame_count / target_total_frames) * 100) if target_total_frames > 0 else 0
                        self.status_callback(f"状态：处理中 {progress}%")
                        
                    # 检查是否已处理完所有需要的帧
                    if frame_count >= target_total_frames:
                        break
            else:
                # 如果帧率相同或无法获取原始帧率，则正常处理
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                        
                    # 调整帧大小
                    resized_frame = cv2.resize(frame, (width, height))
                    out.write(resized_frame)
                    
                    # 更新进度
                    frame_count += 1
                    if self.status_callback and frame_count % 30 == 0:  # 每30帧更新一次状态
                        progress = int((frame_count / total_frames) * 100) if total_frames > 0 else 0
                        self.status_callback(f"状态：处理中 {progress}%")
            
            # 释放资源
            cap.release()
            out.release()
            
            if self.status_callback:
                self.status_callback(f"状态：视频处理完成，保存至 {output_file}")
                
            return True, output_file
            
        except Exception as e:
            if cap.isOpened():
                cap.release()
            if 'out' in locals() and out:
                out.release()
            if self.status_callback:
                self.status_callback(f"状态：处理失败 - {str(e)}")
            return False, str(e)
    
    def extract_frames(self, video_path, output_dir=None, interval=1):
        """从视频中提取帧
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录，默认为save_path
            interval: 提取间隔（秒）
            
        Returns:
            bool: 是否成功
            int: 提取的帧数
        """
        if not os.path.exists(video_path):
            if self.status_callback:
                self.status_callback("状态：视频文件不存在")
            return False, 0
            
        # 设置输出目录
        if output_dir is None:
            output_dir = self.save_path
            
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                if self.status_callback:
                    self.status_callback(f"状态：创建输出目录失败 - {str(e)}")
                return False, 0
        
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            if self.status_callback:
                self.status_callback("状态：无法打开视频文件")
            return False, 0
            
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 25  # 默认25fps
                
            # 计算帧间隔
            frame_interval = int(fps * interval)
            if frame_interval < 1:
                frame_interval = 1
                
            # 提取帧
            count = 0
            frame_count = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # 按间隔保存帧
                if frame_count % frame_interval == 0:
                    frame_path = os.path.join(output_dir, f"frame_{count:04d}.jpg")
                    cv2.imwrite(frame_path, frame)
                    count += 1
                    
                frame_count += 1
                
                # 更新状态
                if self.status_callback and frame_count % 30 == 0:
                    self.status_callback(f"状态：已提取 {count} 帧")
            
            cap.release()
            
            if self.status_callback:
                self.status_callback(f"状态：帧提取完成，共 {count} 帧")
                
            return True, count
            
        except Exception as e:
            if cap.isOpened():
                cap.release()
            if self.status_callback:
                self.status_callback(f"状态：帧提取失败 - {str(e)}")
            return False, 0