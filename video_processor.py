import cv2
import os
from datetime import datetime
from PyQt5.QtCore import QObject
from concurrent.futures import ThreadPoolExecutor


class VideoProcessor(QObject):
    """
    一个用于转换视频文件和提取帧的视频处理类。
    利用多线程提高效率。
    """

    def __init__(self, max_workers=4):
        """
        初始化 VideoProcessor。

        :param max_workers: 线程池中最大工作线程数，默认为 4。
        """
        super().__init__()
        self.status_callback = None
        self.save_path = os.getcwd()
        self.max_workers = max_workers

    def set_status_callback(self, callback):
        """
        设置状态回调函数。

        :param callback: 接受字符串参数的回调函数。
        """
        self.status_callback = callback

    def set_save_path(self, path):
        """
        设置输出文件的保存路径。

        :param path: 文件将保存的目录路径。
        """
        self.save_path = path

    def _process_frame(self, frame, width, height):
        """
        处理单个帧的辅助函数。

        :param frame: 要处理的输入帧。
        :param width: 目标宽度。
        :param height: 目标高度。
        :return: 调整大小后的帧。
        """
        return cv2.resize(frame, (width, height))

    def process_video(self, input_file, width, height, fps, output_format="mp4", buffer_size=100):
        """
        通过调整分辨率和帧率处理视频文件，然后将其保存为新文件。

        :param input_file: 输入视频文件的路径。
        :param width: 目标宽度（像素）。
        :param height: 目标高度（像素）。
        :param fps: 目标每秒帧数。
        :param output_format: 输出文件格式，默认为 "mp4"。
        :param buffer_size: 帧缓冲区大小，默认为 100。
        :return: 元组 (success: bool, result: str) - 成功标志和输出文件路径或错误消息。
        """
        # 验证输入文件
        if not input_file or not os.path.exists(input_file):
            if self.status_callback:
                self.status_callback("状态：请选择有效视频文件")
            return False, "输入文件不存在"

        # 验证参数
        if width <= 0 or height <= 0 or fps <= 0:
            return False, "无效的宽度、高度或帧率参数"

        # 打开视频文件
        cap = cv2.VideoCapture(input_file)
        if not cap.isOpened():
            if self.status_callback:
                self.status_callback("状态：无法打开视频文件")
            return False, "无法打开视频文件"

        try:
            # 根据输出格式设置编码器
            ext = output_format.lower()
            if ext == "avi":
                fourcc = cv2.VideoWriter_fourcc(*"XVID")
            else:
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # 使用高兼容性的 mp4v 编码器

            # 生成带有时间戳的输出文件名
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.save_path, f"{base_name}_{timestamp}.{ext}")

            # 获取视频属性
            original_fps = cap.get(cv2.CAP_PROP_FPS) or 25
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # 创建视频写入器
            out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
            if not out.isOpened():
                cap.release()
                return False, "无法创建输出文件"

            # 初始化帧缓冲区和计数器
            frame_buffer = []
            frame_count = 0
            target_total_frames = total_frames

            # 如果帧率不同，调整帧采样
            if abs(original_fps - fps) > 0.1:
                frame_ratio = original_fps / fps
                target_total_frames = int(total_frames / frame_ratio)

            # 使用线程池处理帧
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    # 如果帧率不同，调整帧位置
                    if abs(original_fps - fps) > 0.1:
                        current_pos = int(frame_count * frame_ratio)
                        cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos)

                    # 提交帧处理任务
                    future = executor.submit(self._process_frame, frame, width, height)
                    frame_buffer.append(future)
                    frame_count += 1

                    # 当缓冲区满或处理完成时写入帧
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

            # 写入剩余的帧
            for future in frame_buffer:
                out.write(future.result())

            # 释放资源
            cap.release()
            out.release()

            # 报告完成
            if self.status_callback:
                self.status_callback(f"状态：视频处理完成，保存至 {output_file}")
            return True, output_file

        except Exception as e:
            # 出错时清理
            if cap.isOpened():
                cap.release()
            if "out" in locals():
                out.release()
            if self.status_callback:
                self.status_callback(f"状态：处理失败 - {str(e)}")
            return False, str(e)

    def extract_frames(self, video_path, output_dir=None, interval=1, batch_size=50):
        """
        从视频中提取帧并将其保存为图像文件。

        :param video_path: 输入视频文件的路径。
        :param output_dir: 保存帧的目录，如果为 None，则默认为 save_path。
        :param interval: 提取帧之间的间隔（秒），默认为 1。
        :param batch_size: 每批处理的帧数，默认为 50。
        :return: 元组 (success: bool, result: int or str) - 成功标志和帧数或错误消息。
        """
        # 验证视频文件
        if not os.path.exists(video_path):
            if self.status_callback:
                self.status_callback("状态：视频文件不存在")
            return False, 0

        # 设置并确保输出目录存在
        output_dir = output_dir or self.save_path
        os.makedirs(output_dir, exist_ok=True)

        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            if self.status_callback:
                self.status_callback("状态：无法打开视频文件")
            return False, 0

        try:
            # 根据 FPS 计算帧间隔
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            frame_interval = max(1, int(fps * interval))
            count = 0
            frame_count = 0
            frame_batch = []

            # 读取和处理帧
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # 按指定间隔提取帧
                if frame_count % frame_interval == 0:
                    frame_path = os.path.join(output_dir, f"frame_{count:04d}.jpg")
                    frame_batch.append((frame_path, frame))
                    count += 1

                frame_count += 1

                # 批量保存帧
                if len(frame_batch) >= batch_size or not ret:
                    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                        executor.map(lambda x: cv2.imwrite(x[0], x[1]), frame_batch)
                    frame_batch.clear()

                    # 更新进度
                    if self.status_callback and frame_count % 30 == 0:
                        self.status_callback(f"状态：已提取 {count} 帧")

            # 释放资源
            cap.release()

            # 报告完成
            if self.status_callback:
                self.status_callback(f"状态：帧提取完成，共 {count} 帧")
            return True, count

        except Exception as e:
            # 出错时清理
            if cap.isOpened():
                cap.release()
            if self.status_callback:
                self.status_callback(f"状态：帧提取失败 - {str(e)}")
            return False, 0