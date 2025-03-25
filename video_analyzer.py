# video_analyzer.py
import cv2
import numpy as np
import os
import torch
from PyQt5.QtCore import QObject, pyqtSignal
from ultralytics import YOLO


class VideoAnalyzer(QObject):
    """视频分析类，负责视频智能分析功能，包括人脸、车辆和行人检测"""
    
    def __init__(self):
        super().__init__()
        self.analyzing = False
        self.detection_types = []
        self.models = {}
        self.face_cascade = None
        self.yolo_model = None
        self.model_path = None
        self.status_callback = None
        
        # GPU性能配置
        self.gpu_enabled = True  # 是否启用GPU
        self.half_precision = False  # 是否使用半精度(FP16)
        self.batch_size = 1  # 批处理大小
        
        # 检测GPU是否可用
        self.device = self._detect_device()
        
        # 初始化模型目录
        self.models_dir = os.path.join(os.getcwd(), 'models')
        
        # 加载人脸检测模型
        self._load_face_cascade()
        
        # 扫描可用的YOLO模型
        self._scan_yolo_models()
        
        # 如果有GPU，设置CUDA缓存
        if self.device.type == "cuda":
            # 清理CUDA缓存
            torch.cuda.empty_cache()
            # 设置CUDA流水线并行化
            torch.backends.cudnn.benchmark = True
    
    def _detect_device(self):
        """检测可用的设备（GPU或CPU）"""
        if torch.cuda.is_available():
            device = torch.device("cuda:0")
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # 转换为GB
            cuda_version = torch.version.cuda if hasattr(torch.version, 'cuda') else "未知"
            if self.status_callback:
                self.status_callback(f"状态：已检测到GPU: {gpu_name}，显存: {gpu_memory:.2f}GB，CUDA版本: {cuda_version}，将使用GPU加速")
            return device
        else:
            if self.status_callback:
                self.status_callback("状态：未检测到GPU，将使用CPU运行")
            return torch.device("cpu")
    
    def set_status_callback(self, callback):
        """设置状态回调函数"""
        self.status_callback = callback
        # 重新检测设备并更新状态
        self.device = self._detect_device()
    
    def _load_face_cascade(self):
        """加载OpenCV人脸检测级联分类器"""
        try:
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
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
        """扫描models目录下的YOLOv8模型"""
        self.models = {}
        if not os.path.exists(self.models_dir):
            if self.status_callback:
                self.status_callback("状态：模型目录不存在")
            return
            
        for file in os.listdir(self.models_dir):
            if file.endswith('.pt') and 'yolov8' in file.lower():
                model_path = os.path.join(self.models_dir, file)
                self.models[file] = model_path
        
        if not self.models and self.status_callback:
            self.status_callback("状态：未找到YOLOv8模型")
    
    def get_available_models(self):
        """获取可用的YOLOv8模型列表"""
        return list(self.models.keys())
    
    def load_yolo_model(self, model_name):
        """加载指定的YOLOv8模型"""
        if model_name not in self.models:
            if self.status_callback:
                self.status_callback(f"状态：模型 {model_name} 不存在")
            return False
            
        try:
            # 如果有旧模型，先清理内存
            if self.yolo_model and self.device.type == "cuda":
                del self.yolo_model
                torch.cuda.empty_cache()
                
            model_path = self.models[model_name]
            # 使用检测到的设备加载模型
            device_str = "GPU" if self.device.type == "cuda" and self.gpu_enabled else "CPU"
            self.yolo_model = YOLO(model_path)
            
            # 设置模型运行设备
            if self.device.type == "cuda" and self.gpu_enabled:
                self.yolo_model.to(self.device)
                
                # 如果启用半精度，转换模型为FP16
                if self.half_precision:
                    self.yolo_model.model.half()
                    precision_str = "FP16半精度"
                else:
                    precision_str = "FP32全精度"
                    
                self.model_path = model_path
                if self.status_callback:
                    self.status_callback(f"状态：已加载模型 {model_name}，使用{device_str}推理，{precision_str}，批处理大小: {self.batch_size}")
            else:
                self.model_path = model_path
                if self.status_callback:
                    self.status_callback(f"状态：已加载模型 {model_name}，使用{device_str}推理")
                    
            return True
        except Exception as e:
            if self.status_callback:
                self.status_callback(f"状态：加载模型失败 - {str(e)}")
            return False
    
    def set_detection_types(self, detection_types):
        """设置检测类型
        
        Args:
            detection_types: 检测类型列表，可包含 'face', 'vehicle', 'person'
        """
        self.detection_types = detection_types
    
    def start_analysis(self):
        """开始视频分析"""
        if 'vehicle' in self.detection_types or 'person' in self.detection_types:
            if not self.yolo_model:
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
            
    def set_gpu_config(self, enabled=True, half_precision=False, batch_size=1):
        """设置GPU配置
        
        Args:
            enabled: 是否启用GPU
            half_precision: 是否使用半精度(FP16)
            batch_size: 批处理大小
        """
        # 检查是否有可用的GPU
        if enabled and self.device.type != "cuda":
            if self.status_callback:
                self.status_callback("状态：未检测到GPU，无法启用GPU加速")
            return False
            
        old_config = (self.gpu_enabled, self.half_precision, self.batch_size)
        self.gpu_enabled = enabled
        self.half_precision = half_precision if enabled else False
        self.batch_size = batch_size if batch_size > 0 else 1
        
        # 如果配置发生变化且模型已加载，需要重新加载模型应用新配置
        if old_config != (self.gpu_enabled, self.half_precision, self.batch_size) and self.yolo_model is not None:
            # 获取当前模型名称
            current_model = None
            for name, path in self.models.items():
                if path == self.model_path:
                    current_model = name
                    break
                    
            if current_model:
                # 重新加载模型以应用新配置
                self.load_yolo_model(current_model)
                
        # 更新状态信息
        if self.status_callback:
            if enabled:
                precision_str = "FP16半精度" if half_precision else "FP32全精度"
                self.status_callback(f"状态：GPU加速已启用，{precision_str}，批处理大小: {batch_size}")
            else:
                self.status_callback("状态：GPU加速已禁用，将使用CPU运行")
                
        return True
    
    def analyze_frame(self, frame):
        """分析视频帧
        
        Args:
            frame: 输入视频帧
            
        Returns:
            analyzed_frame: 分析后的视频帧（带有检测标记）
        """
        if frame is None or not self.analyzing:
            return frame
            
        # 创建帧的副本用于绘制
        analyzed_frame = frame.copy()
        
        # 人脸检测
        if 'face' in self.detection_types and self.face_cascade:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            for (x, y, w, h) in faces:
                cv2.rectangle(analyzed_frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                cv2.putText(analyzed_frame, 'Face', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
        
        # 使用YOLOv8进行车辆和行人检测
        if ('vehicle' in self.detection_types or 'person' in self.detection_types) and self.yolo_model:
            try:
                # 使用YOLOv8进行检测，指定设备和批处理大小
                device_to_use = self.device if self.gpu_enabled else torch.device("cpu")
                results = self.yolo_model(frame, device=device_to_use, batch=self.batch_size)
                
                # 处理检测结果
                for result in results:
                    boxes = result.boxes.cpu().numpy()
                    for box in boxes:
                        # 获取边界框坐标
                        x1, y1, x2, y2 = box.xyxy[0].astype(int)
                        # 获取置信度
                        conf = box.conf[0]
                        # 获取类别ID和名称
                        cls_id = int(box.cls[0])
                        cls_name = result.names[cls_id]
                        
                        # 根据检测类型过滤结果
                        if ('vehicle' in self.detection_types and cls_name in ['car', 'truck', 'bus', 'motorcycle']) or \
                           ('person' in self.detection_types and cls_name == 'person'):
                            # 为不同类别设置不同颜色
                            color = (0, 255, 0) if cls_name == 'person' else (0, 0, 255)  # 绿色为行人，红色为车辆
                            
                            # 绘制边界框和标签
                            cv2.rectangle(analyzed_frame, (x1, y1), (x2, y2), color, 2)
                            label = f'{cls_name} {conf:.2f}'
                            cv2.putText(analyzed_frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            except Exception as e:
                if self.status_callback:
                    self.status_callback(f"状态：检测过程中出错 - {str(e)}")
        
        return analyzed_frame