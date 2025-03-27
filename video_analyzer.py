import cv2
import numpy as np
import os
import torch
from PyQt5.QtCore import QObject
from ultralytics import YOLO
import concurrent.futures

class VideoAnalyzer(QObject):
    """视频分析类，负责视频智能分析功能，包括人脸、车辆和行人检测"""

    def __init__(self):
        """初始化视频分析器"""
        super().__init__()
        self.analyzing = False  # 是否正在分析
        self.detection_types = []  # 检测类型列表
        self.models = {}  # 可用的 YOLO 模型
        self.face_cascade = None  # 人脸检测分类器
        self.yolo_model = None  # YOLOv8 模型
        self.model_path = None  # 当前加载的模型路径
        self.status_callback = None  # 状态回调函数

        # GPU 配置
        self.gpu_enabled = True  # 默认启用 GPU
        self.batch_size = 1  # 批处理大小

        # 检测可用设备
        self.device = self._detect_device()

        # 初始化模型目录
        self.models_dir = os.path.join(os.getcwd(), "models")

        # 加载人脸检测模型和扫描 YOLO 模型
        self._load_face_cascade()
        self._scan_yolo_models()

        # 自动加载第一个可用 YOLO 模型
        if self.models:
            first_model = list(self.models.keys())[0]
            self.load_yolo_model(first_model)

        # 如果有 GPU，优化 CUDA 设置；否则优化 CPU 多线程
        if self.device.type == "cuda":
            torch.cuda.empty_cache()  # 清理 CUDA 缓存
            torch.backends.cudnn.benchmark = True  # 启用 CUDA 性能优化
        else:
            num_threads = os.cpu_count()  # 获取 CPU 核心数
            torch.set_num_threads(num_threads)  # 设置 PyTorch 线程数
            if self.status_callback:
                self.status_callback(f"状态：使用 CPU，多线程数: {num_threads}")

    def _detect_device(self):
        """检测可用设备（GPU 或 CPU）

        Returns:
            torch.device: 检测到的设备
        """
        if torch.cuda.is_available():
            device = torch.device("cuda:0")
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            cuda_version = torch.version.cuda or "未知"
            if self.status_callback:
                self.status_callback(
                    f"状态：已检测到GPU: {gpu_name}，显存: {gpu_memory:.2f}GB，CUDA版本: {cuda_version}"
                )
            return device
        else:
            if self.status_callback:
                self.status_callback("状态：未检测到GPU，将使用CPU运行")
            return torch.device("cpu")

    def set_status_callback(self, callback):
        """设置状态回调函数"""
        self.status_callback = callback
        self.device = self._detect_device()

    def _load_face_cascade(self):
        """加载 OpenCV 人脸检测级联分类器"""
        try:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            if self.face_cascade.empty():
                if self.status_callback:
                    self.status_callback("状态：无法加载人脸检测模型")
                return False
            return True
        except Exception as e:
            if self.status_callback:
                self.status_callback(f"状态：加载人脸检测模型失败 - {str(e)}")
            return False

    def _scan_yolo_models(self):
        """扫描 models 目录下的 YOLOv8 模型"""
        self.models = {}
        if not os.path.exists(self.models_dir):
            if self.status_callback:
                self.status_callback("状态：模型目录不存在")
            return

        for file in os.listdir(self.models_dir):
            if file.endswith(".pt") and "yolo" in file.lower():
                self.models[file] = os.path.join(self.models_dir, file)

        if not self.models and self.status_callback:
            self.status_callback("状态：未找到YOLO模型")

    def get_available_models(self):
        """获取可用的 YOLOv8 模型列表"""
        return list(self.models.keys())

    def load_yolo_model(self, model_name):
        """加载指定的 YOLOv8 模型"""
        if model_name not in self.models:
            if self.status_callback:
                self.status_callback(f"状态：模型 {model_name} 不存在")
            return False

        try:
            if self.yolo_model and self.device.type == "cuda":
                del self.yolo_model
                torch.cuda.empty_cache()

            model_path = self.models[model_name]
            self.yolo_model = YOLO(model_path)
            device_str = "GPU" if self.gpu_enabled and self.device.type == "cuda" else "CPU"

            if self.gpu_enabled and self.device.type == "cuda":
                self.yolo_model.to(self.device)
            else:
                self.yolo_model.to("cpu")

            self.model_path = model_path
            if self.status_callback:
                self.status_callback(f"状态：已加载模型 {model_name}，使用{device_str}推理")
            return True
        except Exception as e:
            if self.status_callback:
                self.status_callback(f"状态：加载模型失败 - {str(e)}")
            return False

    def set_detection_types(self, detection_types):
        """设置检测类型"""
        self.detection_types = detection_types
        if self.status_callback:
            self.status_callback(f"状态：检测类型已更新为 {', '.join(detection_types)}")

    def start_analysis(self):
        """开始视频分析"""
        if ("vehicle" in self.detection_types or "person" in self.detection_types) and not self.yolo_model:
            if self.status_callback:
                self.status_callback("状态：请先加载YOLOv8模型")
            return False

        self.analyzing = True
        if self.status_callback:
            self.status_callback("状态：视频分析已启动")
        return True

    def stop_analysis(self):
        """停止视频分析"""
        self.analyzing = False
        if self.status_callback:
            self.status_callback("状态：视频分析已停止")

    def set_gpu_config(self, enabled=True, batch_size=1):
        """设置 GPU 配置"""
        if enabled and self.device.type != "cuda":
            if self.status_callback:
                self.status_callback("状态：未检测到GPU，无法启用GPU加速")
            return False

        old_config = (self.gpu_enabled, self.batch_size)
        self.gpu_enabled = enabled
        self.batch_size = max(batch_size, 1)

        if old_config != (self.gpu_enabled, self.batch_size) and self.yolo_model:
            current_model = next(
                (name for name, path in self.models.items() if path == self.model_path), None
            )
            if current_model:
                self.load_yolo_model(current_model)

        if self.status_callback:
            self.status_callback(
                f"状态：GPU加速已{'启用' if enabled else '禁用'}，批处理大小: {self.batch_size}"
            )
        return True

    def _detect_faces(self, gray_frame, scale_factor=0.5):
        """多线程辅助函数：检测人脸"""
        small_frame = cv2.resize(gray_frame, (0, 0), fx=scale_factor, fy=scale_factor)
        faces = self.face_cascade.detectMultiScale(small_frame, 1.1, 4)
        return [(int(x / scale_factor), int(y / scale_factor), int(w / scale_factor), int(h / scale_factor)) for (x, y, w, h) in faces]

    def _preprocess_frame(self, frame, input_size=640):
        """图像预处理函数：调整大小并转换为张量"""
        resized_frame = cv2.resize(frame, (input_size, input_size))
        return resized_frame

    def analyze_frame(self, frame):
        """分析视频帧"""
        if frame is None or not self.analyzing:
            return frame

        analyzed_frame = frame.copy()
        height, width = frame.shape[:2]

        # 人脸检测（优化：图像缩放 + 多线程）
        if "face" in self.detection_types and self.face_cascade:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._detect_faces, gray, scale_factor=0.5)
                faces = future.result()

            for (x, y, w, h) in faces:
                cv2.rectangle(analyzed_frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(analyzed_frame, "Face", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

        # YOLOv8 检测（优化：多线程预处理 + 多核推理）
        if ("vehicle" in self.detection_types or "person" in self.detection_types) and self.yolo_model:
            try:
                input_size = 640  # YOLOv8 默认输入尺寸
                # 使用多线程预处理图像
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._preprocess_frame, frame, input_size)
                    resized_frame = future.result()

                device_to_use = self.device if self.gpu_enabled and self.device.type == "cuda" else torch.device("cpu")
                results = self.yolo_model(resized_frame, device=device_to_use, batch=self.batch_size)

                for result in results:
                    boxes = result.boxes.cpu().numpy()
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].astype(int)
                        # 坐标映射回原始尺寸
                        x1, y1 = int(x1 * width / input_size), int(y1 * height / input_size)
                        x2, y2 = int(x2 * width / input_size), int(y2 * height / input_size)
                        conf = box.conf[0]
                        cls_id = int(box.cls[0])
                        cls_name = result.names[cls_id]

                        if ("vehicle" in self.detection_types and cls_name in ["car", "truck", "bus", "motorcycle"]) or \
                           ("person" in self.detection_types and cls_name == "person"):
                            color = (0, 255, 0) if cls_name == "person" else (0, 0, 255)
                            cv2.rectangle(analyzed_frame, (x1, y1), (x2, y2), color, 2)
                            label = f"{cls_name} {conf:.2f}"
                            cv2.putText(analyzed_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            except Exception as e:
                if self.status_callback:
                    self.status_callback(f"状态：检测过程中出错 - {str(e)}")

        return analyzed_frame