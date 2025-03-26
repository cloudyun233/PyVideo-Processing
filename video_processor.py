import cv2
import os
from datetime import datetime
from PyQt5.QtCore import QObject
from concurrent.futures import ThreadPoolExecutor
import numpy as np

class VideoProcessor(QObject):
    def __init__(self, max_workers=4):
        super().__init__()
        self.status_callback = None
        self.save_path = os.getcwd()
        self.max_workers = max_workers  # 可根据CPU核心数调整
        
    # 原有的set_status_callback和set_save_path保持不变
    
    def _process_frame(self, frame, width, height):
        """处理单帧的辅助函数"""
        return cv2.resize(frame, (width, height))
    
    def process_video(self, input_file, width, height, fps, output_format="mp4", buffer_size=100):
        """优化后的视频处理函数"""
        if not input_file or not os.path.exists(input_file):
            if self.status_callback:
                self.status_callback("状态：请选择有效视频文件")
            return False, "输入文件不存在"

        # 提前检查参数
        if width <= 0 or height <= 0 or fps <= 0:
            return False, "无效的宽度、高度或帧率参数"

        cap = cv2.VideoCapture(input_file)
        if not cap.isOpened():
            if self.status_callback:
                self.status_callback("状态：无法打开视频文件")
            return False, "无法打开视频文件"

        try:
            # 使用更兼容的编码器选项
            ext = output_format.lower()
            if ext == "avi":
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
            else:
                # 尝试使用H264编码器（更兼容Windows）
                try:
                    fourcc = cv2.VideoWriter_fourcc(*'H264')
                except Exception:
                    # 如果H264不可用，尝试其他常用编码器
                    for codec in ['avc1', 'X264', 'mp4v']:
                        try:
                            fourcc = cv2.VideoWriter_fourcc(*codec)
                            print(f"使用编码器: {codec}")
                            break
                        except Exception:
                            continue
                    else:
                        # 如果所有尝试都失败，使用基本编码器
                        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                        print("使用基本编码器: mp4v")
            
            # 输出文件设置
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.save_path, f"{base_name}_{timestamp}.{ext}")
            
            # 获取视频信息
            original_fps = cap.get(cv2.CAP_PROP_FPS) or 25
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 创建视频写入器
            out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
            if not out.isOpened():
                cap.release()
                return False, "无法创建输出文件"
            
            frame_buffer = []
            frame_count = 0
            target_total_frames = total_frames
            
            # 如果帧率不同，计算采样率
            if abs(original_fps - fps) > 0.1:
                frame_ratio = original_fps / fps
                target_total_frames = int(total_frames / frame_ratio)
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                        
                    # 计算目标帧位置
                    if abs(original_fps - fps) > 0.1:
                        current_pos = int(frame_count * frame_ratio)
                        cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos)
                    
                    # 使用线程池处理帧
                    future = executor.submit(self._process_frame, frame, width, height)
                    frame_buffer.append(future)
                    frame_count += 1
                    
                    # 当缓冲区满时写入
                    if len(frame_buffer) >= buffer_size or frame_count >= target_total_frames:
                        for future in frame_buffer:
                            resized_frame = future.result()
                            out.write(resized_frame)
                        frame_buffer.clear()
                        
                        # 更新进度
                        if self.status_callback and frame_count % 30 == 0:
                            progress = int((frame_count / target_total_frames) * 100)
                            self.status_callback(f"状态：处理中 {progress}%")
                    
                    if frame_count >= target_total_frames:
                        break
            
            # 处理剩余的帧
            for future in frame_buffer:
                out.write(future.result())
            
            cap.release()
            out.release()
            
            if self.status_callback:
                self.status_callback(f"状态：视频处理完成，保存至 {output_file}")
            return True, output_file
            
        except Exception as e:
            if cap.isOpened(): cap.release()
            if 'out' in locals(): out.release()
            if self.status_callback:
                self.status_callback(f"状态：处理失败 - {str(e)}")
            return False, str(e)
    
    def extract_frames(self, video_path, output_dir=None, interval=1, batch_size=50):
        """优化后的帧提取函数"""
        if not os.path.exists(video_path):
            if self.status_callback:
                self.status_callback("状态：视频文件不存在")
            return False, 0
            
        output_dir = output_dir or self.save_path
        os.makedirs(output_dir, exist_ok=True)
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            if self.status_callback:
                self.status_callback("状态：无法打开视频文件")
            return False, 0
            
        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            frame_interval = max(1, int(fps * interval))
            count = 0
            frame_count = 0
            frame_batch = []
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                    
                if frame_count % frame_interval == 0:
                    frame_path = os.path.join(output_dir, f"frame_{count:04d}.jpg")
                    frame_batch.append((frame_path, frame))
                    count += 1
                    
                frame_count += 1
                
                # 批量写入
                if len(frame_batch) >= batch_size or not ret:
                    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                        executor.map(lambda x: cv2.imwrite(x[0], x[1]), frame_batch)
                    frame_batch.clear()
                    
                    if self.status_callback and frame_count % 30 == 0:
                        self.status_callback(f"状态：已提取 {count} 帧")
            
            cap.release()
            if self.status_callback:
                self.status_callback(f"状态：帧提取完成，共 {count} 帧")
            return True, count
            
        except Exception as e:
            if cap.isOpened(): cap.release()
            if self.status_callback:
                self.status_callback(f"状态：帧提取失败 - {str(e)}")
            return False, 0