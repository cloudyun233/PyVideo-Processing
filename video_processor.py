import cv2
import os
from datetime import datetime
from PyQt5.QtCore import QObject
from concurrent.futures import ThreadPoolExecutor


class VideoProcessor(QObject):
    """
    A video processing class for converting video files and extracting frames.
    Utilizes multi-threading for improved efficiency.
    """

    def __init__(self, max_workers=4):
        """
        Initialize the VideoProcessor.

        :param max_workers: Maximum number of worker threads in the thread pool, defaults to 4.
        """
        super().__init__()
        self.status_callback = None
        self.save_path = os.getcwd()
        self.max_workers = max_workers

    def set_status_callback(self, callback):
        """
        Set the status callback function.

        :param callback: A callback function that accepts a string parameter.
        """
        self.status_callback = callback

    def set_save_path(self, path):
        """
        Set the save path for output files.

        :param path: The directory path where files will be saved.
        """
        self.save_path = path

    def _process_frame(self, frame, width, height):
        """
        Helper function to process a single frame.

        :param frame: The input frame to process.
        :param width: Target width for resizing.
        :param height: Target height for resizing.
        :return: The resized frame.
        """
        return cv2.resize(frame, (width, height))

    def process_video(self, input_file, width, height, fps, output_format="mp4", buffer_size=100):
        """
        Process a video file by adjusting resolution and frame rate, then save it as a new file.

        :param input_file: Path to the input video file.
        :param width: Target width in pixels.
        :param height: Target height in pixels.
        :param fps: Target frames per second.
        :param output_format: Output file format, defaults to "mp4".
        :param buffer_size: Size of the frame buffer, defaults to 100.
        :return: Tuple (success: bool, result: str) - Success flag and either output file path or error message.
        """
        # Validate input file
        if not input_file or not os.path.exists(input_file):
            if self.status_callback:
                self.status_callback("状态：请选择有效视频文件")
            return False, "输入文件不存在"

        # Validate parameters
        if width <= 0 or height <= 0 or fps <= 0:
            return False, "无效的宽度、高度或帧率参数"

        # Open the video file
        cap = cv2.VideoCapture(input_file)
        if not cap.isOpened():
            if self.status_callback:
                self.status_callback("状态：无法打开视频文件")
            return False, "无法打开视频文件"

        try:
            # Set the encoder based on output format
            ext = output_format.lower()
            if ext == "avi":
                fourcc = cv2.VideoWriter_fourcc(*"XVID")
            else:
                fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # Use highly compatible mp4v encoder

            # Generate output file name with timestamp
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.save_path, f"{base_name}_{timestamp}.{ext}")

            # Get video properties
            original_fps = cap.get(cv2.CAP_PROP_FPS) or 25
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # Create video writer
            out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
            if not out.isOpened():
                cap.release()
                return False, "无法创建输出文件"

            # Initialize frame buffer and counters
            frame_buffer = []
            frame_count = 0
            target_total_frames = total_frames

            # Adjust frame sampling if FPS differs
            if abs(original_fps - fps) > 0.1:
                frame_ratio = original_fps / fps
                target_total_frames = int(total_frames / frame_ratio)

            # Process frames using a thread pool
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    # Adjust frame position if FPS differs
                    if abs(original_fps - fps) > 0.1:
                        current_pos = int(frame_count * frame_ratio)
                        cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos)

                    # Submit frame processing task
                    future = executor.submit(self._process_frame, frame, width, height)
                    frame_buffer.append(future)
                    frame_count += 1

                    # Write frames when buffer is full or processing is complete
                    if len(frame_buffer) >= buffer_size or frame_count >= target_total_frames:
                        for future in frame_buffer:
                            resized_frame = future.result()
                            out.write(resized_frame)
                        frame_buffer.clear()

                        # Update progress
                        if self.status_callback and frame_count % 30 == 0:
                            progress = int((frame_count / target_total_frames) * 100)
                            self.status_callback(f"状态：处理中 {progress}%")

                    if frame_count >= target_total_frames:
                        break

            # Write any remaining frames
            for future in frame_buffer:
                out.write(future.result())

            # Release resources
            cap.release()
            out.release()

            # Report completion
            if self.status_callback:
                self.status_callback(f"状态：视频处理完成，保存至 {output_file}")
            return True, output_file

        except Exception as e:
            # Clean up on error
            if cap.isOpened():
                cap.release()
            if "out" in locals():
                out.release()
            if self.status_callback:
                self.status_callback(f"状态：处理失败 - {str(e)}")
            return False, str(e)

    def extract_frames(self, video_path, output_dir=None, interval=1, batch_size=50):
        """
        Extract frames from a video and save them as image files.

        :param video_path: Path to the input video file.
        :param output_dir: Directory to save frames, defaults to save_path if None.
        :param interval: Interval in seconds between extracted frames, defaults to 1.
        :param batch_size: Number of frames to process in a batch, defaults to 50.
        :return: Tuple (success: bool, result: int or str) - Success flag and either frame count or error message.
        """
        # Validate video file
        if not os.path.exists(video_path):
            if self.status_callback:
                self.status_callback("状态：视频文件不存在")
            return False, 0

        # Set and ensure output directory exists
        output_dir = output_dir or self.save_path
        os.makedirs(output_dir, exist_ok=True)

        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            if self.status_callback:
                self.status_callback("状态：无法打开视频文件")
            return False, 0

        try:
            # Calculate frame interval based on FPS
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            frame_interval = max(1, int(fps * interval))
            count = 0
            frame_count = 0
            frame_batch = []

            # Read and process frames
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # Extract frame at specified interval
                if frame_count % frame_interval == 0:
                    frame_path = os.path.join(output_dir, f"frame_{count:04d}.jpg")
                    frame_batch.append((frame_path, frame))
                    count += 1

                frame_count += 1

                # Save frames in batches
                if len(frame_batch) >= batch_size or not ret:
                    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                        executor.map(lambda x: cv2.imwrite(x[0], x[1]), frame_batch)
                    frame_batch.clear()

                    # Update progress
                    if self.status_callback and frame_count % 30 == 0:
                        self.status_callback(f"状态：已提取 {count} 帧")

            # Release resources
            cap.release()

            # Report completion
            if self.status_callback:
                self.status_callback(f"状态：帧提取完成，共 {count} 帧")
            return True, count

        except Exception as e:
            # Clean up on error
            if cap.isOpened():
                cap.release()
            if self.status_callback:
                self.status_callback(f"状态：帧提取失败 - {str(e)}")
            return False, 0