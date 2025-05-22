# Unity截图 + 豆包AI生图系统 - 项目架构

## 目录结构

```
E:\unity\Program\My project (2)\  [项目根目录]
│
├── Assets\                        [Unity 资源目录]
│   ├── Scripts\                   [Unity 脚本目录]
│   │   └── ScreenshotCapture.cs   [Unity 截图脚本]
│   └── ... (其他 Unity 资源)
│
├── Python\                        [Python 程序目录]
│   ├── src\                       [Python 源代码目录]
│   │   ├── api\                   [API 相关代码]
│   │   │   ├── doubao_api.py      [豆包 API 客户端]
│   │   │   └── doubao_vision_api.py [豆包视觉 API 客户端]
│   │   │
│   │   ├── monitor\               [监控相关代码]
│   │   │   └── image_monitor.py   [图片监控器]
│   │   │
│   │   ├── ui\                    [UI 相关代码]
│   │   │   ├── components.py      [UI 组件]
│   │   │   └── streamlit_app.py   [Streamlit 应用]
│   │   │
│   │   └── utils\                 [工具函数]
│   │       ├── helpers.py         [辅助函数]
│   │       └── prompt.py          [提示词管理]
│   │
│   ├── temp\                      [临时文件目录]
│   ├── main.py                    [Python 主程序]
│   ├── requirements.txt           [依赖包列表]
│   ├── .env                       [环境变量配置]
│   ├── README.md                  [项目说明文档]
│   ├── run.ps1                    [PowerShell 启动脚本]
│   ├── run.bat                    [批处理启动脚本]
│   └── 启动程序.bat                [中文批处理启动脚本]
│
├── Screenshots\                   [截图目录 - 共享目录 1]
│   ├── screenshot1.png            [Unity 生成的截图]
│   ├── screenshot2.png            [Unity 生成的截图]
│   └── ...
│
├── Outputs\                       [输出目录 - 共享目录 2]
│   ├── generated_20230601_123456_screenshot1.png  [Python 生成的图片]
│   ├── generated_20230601_123457_screenshot2.png  [Python 生成的图片]
│   └── ...
│
├── logs\                          [日志目录]
│   └── app.log                    [应用日志文件]
│
├── arc\                           [架构文档目录]
│   └── ...                        [架构相关文档]
│
├── sum\                           [对话总结目录]
│   └── ...                        [对话总结文件]
│
└── paths.json                     [路径配置文件 - 关键连接点]
```

## 数据流程

```
┌─────────────┐     生成截图     ┌─────────────┐     写入配置     ┌─────────────┐
│             │ ───────────────> │             │ ───────────────> │             │
│  Unity游戏  │                  │ Screenshots │                  │  paths.json │
│             │                  │    目录     │                  │             │
└─────────────┘                  └─────────────┘                  └─────────────┘
                                       │                                │
                                       │ 监控新文件                      │ 读取配置
                                       ▼                                │
┌─────────────┐     保存结果     ┌─────────────┐      读取配置      ┌─────────────┐
│             │ <─────────────── │             │ <───────────────── │             │
│   Outputs   │                  │  Python程序 │                    │  Python程序 │
│    目录     │                  │ (监控线程)  │                    │  (主线程)   │
└─────────────┘                  └─────────────┘                    └─────────────┘
      │                                │                                  │
      │                                │                                  │
      │                                │ 调用API                          │ 启动
      │                                ▼                                  │
      │                          ┌─────────────┐                          │
      │                          │             │                          │
      │                          │  豆包API    │                          │
      │                          │             │                          │
      │                          └─────────────┘                          │
      │                                                                   │
      │                                                                   │
      │                          ┌─────────────┐                          │
      └────────────────────────> │             │ <────────────────────────┘
                                 │ Streamlit UI│
                                 │             │
                                 └─────────────┘
```

## 主要组件说明

1. **Unity游戏**：
   - 通过 `ScreenshotCapture.cs` 脚本捕获游戏截图
   - 将截图保存到 `Screenshots` 目录
   - 生成 `paths.json` 配置文件，记录所有目录的路径信息

2. **Python程序**：
   - **主线程**：
     - 读取 `paths.json` 配置文件获取路径信息
     - 启动监控线程和Streamlit UI
   - **监控线程**：
     - 监控 `Screenshots` 目录中的新文件
     - 调用豆包视觉理解API分析图片生成提示词
     - 调用豆包图像生成API生成新图片
     - 将生成的图片保存到 `Outputs` 目录
     - 删除处理完成的原始截图

3. **Streamlit UI**：
   - 提供Web界面展示生成结果
   - 允许用户创建图片生成请求
   - 提供图床功能，展示和管理生成的图片

4. **启动脚本**：
   - `run.ps1`：PowerShell启动脚本，负责环境检查、虚拟环境创建和依赖安装
   - `run.bat`/`启动程序.bat`：批处理启动脚本，作为PowerShell脚本的启动器

5. **共享目录**：
   - `Screenshots`：Unity保存截图的目录，Python监控此目录
   - `Outputs`：Python保存生成图片的目录，Streamlit UI展示此目录中的图片
   - `logs`：系统日志目录，记录运行日志

6. **配置文件**：
   - `paths.json`：由Unity生成，记录所有目录的路径信息，Python读取此文件获取路径信息
   - `.env`：环境变量配置文件，包含API密钥等敏感信息

## 工作流程

1. **启动流程**：
   - 用户双击 `启动程序.bat` 或运行 `run.ps1`
   - 脚本检查Python环境，创建虚拟环境（如果不存在）
   - 安装所需依赖
   - 启动主程序 `main.py`

2. **图片处理流程**：
   - Unity游戏通过 `ScreenshotCapture.cs` 捕获截图并保存到 `Screenshots` 目录
   - Python监控线程检测到新图片
   - 调用豆包视觉理解API分析图片内容，生成提示词
   - 使用生成的提示词和豆包生图API生成新图像
   - 将生成的图像保存到 `Outputs` 目录
   - 删除原始截图，避免重复处理

3. **Web界面流程**：
   - Streamlit UI启动并监听 http://localhost:8501
   - 用户可以通过Web界面查看生成的图片
   - 用户可以上传新图片进行处理
   - 用户可以自定义提示词和生成参数

## 关键技术

1. **文件系统监控**：使用 `watchdog` 库监控文件系统变化
2. **API调用**：使用 `requests` 库调用豆包API
3. **图像处理**：使用 `Pillow` 和 `opencv-python` 处理图像
4. **Web界面**：使用 `streamlit` 构建Web界面
5. **环境管理**：使用 `python-dotenv` 管理环境变量
6. **提示词管理**：集中管理提示词，便于统一修改和优化