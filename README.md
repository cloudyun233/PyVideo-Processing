# 视频处理工具包

## 项目描述
本工具包提供了一系列视频处理功能，基于OpenCV和PyQt5开发，已对Windows、Linux和macOS系统进行基本代码适配（Linux和macOS平台未经充分测试）。主要功能模块包括：

1. **视频录制模块**：支持摄像头录制、屏幕录制，可设置分辨率、帧率等参数
2. **视频处理模块**：提供视频剪辑、格式转换、滤镜添加等功能
3. **视频播放模块**：支持多种视频格式播放，可调节播放速度、音量等
4. **视频分析模块**：包含运动检测、目标追踪、视频质量分析等功能

适用于以下场景：
- 视频监控系统开发
- 视频编辑软件开发
- 视频分析应用开发
- 多媒体教学软件开发

## 安装说明
### 系统要求
- 操作系统：Windows 10/11
- Python版本：3.12
- 显卡：推荐支持CUDA 12.4
- 内存：建议4GB以上

### 安装步骤
1. 克隆项目到本地：
```bash
git clone https://github.com/yourusername/python-zyy.git
```
2. 创建并激活虚拟环境：
```bash
python -m venv venv
venv\Scripts\activate
```
3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法
1. 运行主程序：
```bash
python main.py
```
2. 在GUI界面中选择需要的功能模块
3. 按照界面提示进行操作

## 项目结构
```
./
├── gui/               # GUI界面相关代码
│   └── main_window.py
├── video_utils.py     # 视频处理工具函数
├── video_recorder.py  # 视频录制模块
├── video_processor.py # 视频处理模块
├── video_playback.py  # 视频播放模块
├── video_analyzer.py  # 视频分析模块
├── main.py            # 程序入口
└── requirements.txt   # 依赖文件
```

## 贡献指南
1. 请遵循PEP 8代码规范
2. 提交代码前请确保通过所有测试
3. 提交Pull Request时请详细描述修改内容

## 许可证信息
本项目采用MIT许可证，详情请查看LICENSE文件。

## 联系方式
如有任何问题，请联系：
- 邮箱: cloudyun233@gmail.com
