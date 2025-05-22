# Unity截图 + 豆包AI生图系统

这是一个集成了Unity截图和豆包AI生图功能的系统，可以自动监控截图文件夹，使用豆包AI进行图像生成，并提供Streamlit Web界面进行交互。

## 功能特点

- **自动监控**：监控Screenshots文件夹中的新图片，自动处理并生成新图像
- **AI图像生成**：使用豆包AI生成高质量图像，支持多种尺寸和风格
- **视觉理解**：使用豆包视觉理解API分析图片内容，生成精准的提示词
- **Web界面**：提供Streamlit Web界面，支持图床功能和手动图像生成
- **自动适配**：根据原始图片尺寸自动选择最佳的生成尺寸
- **环境自适应**：支持通过环境变量或配置文件设置路径，提高环境适应性

## 系统架构

```
Python/                  # Python项目根目录
├── main.py              # 主程序入口
├── requirements.txt     # 项目依赖
├── run.ps1              # PowerShell启动脚本
├── 启动程序.bat          # 批处理启动脚本
├── .env                 # 环境变量配置
├── src/                 # 源代码目录
│   ├── api/             # API调用模块
│   │   ├── doubao_api.py        # 豆包生图API
│   │   └── doubao_vision_api.py # 豆包视觉理解API
│   ├── monitor/         # 监控模块
│   │   └── image_monitor.py     # 图片监控器
│   ├── ui/              # 用户界面模块
│   │   ├── components.py        # UI组件
│   │   └── streamlit_app.py     # Streamlit应用
│   └── utils/           # 工具模块
│       ├── helpers.py           # 辅助函数
│       └── prompt.py            # 提示词管理
├── logs/                # 日志目录
└── temp/                # 临时文件目录
```

## 工作流程

1. **监控截图**：系统启动后，会监控Screenshots文件夹中的新图片
2. **视觉分析**：当检测到新图片时，使用豆包视觉理解API分析图片内容，生成提示词
3. **图像生成**：使用生成的提示词和豆包生图API生成新图像
4. **保存输出**：将生成的图像保存到Outputs文件夹
5. **删除原图**：处理完成后删除原始截图，以避免重复处理
6. **Web界面**：同时启动Streamlit Web界面，提供图床功能和手动图像生成

## 安装与使用

### 系统要求

- Python 3.8或更高版本
- Windows操作系统（推荐）
- 豆包API密钥

### 快速开始

1. **克隆或下载项目**

2. **配置环境变量**

   创建`.env`文件，添加以下内容：

   ```
   DOUBAO_API_KEY=你的豆包API密钥
   DOUBAO_API_URL=https://ark.cn-beijing.volces.com/api/v3/images/generations
   DOUBAO_MODEL=doubao-seedream-3-0-t2i-250415
   DOUBAO_VISION_API_URL=https://ark.cn-beijing.volces.com/api/v3/chat/completions
   DOUBAO_VISION_MODEL=doubao-1.5-thinking-vision-pro-250428
   ```

3. **启动系统**

   双击`启动程序.bat`或运行`run.ps1`脚本启动系统。脚本会自动：
   - 检查Python环境
   - 创建虚拟环境（如果不存在）
   - 安装所需依赖
   - 启动主程序

4. **使用Web界面**

   系统启动后，访问 http://localhost:8501 打开Streamlit Web界面。

### 文件夹结构

- **Screenshots**：放置需要处理的截图
- **Outputs**：生成的图像输出目录
- **logs**：系统日志目录
- **temp**：临时文件目录

## 配置选项

### 环境变量

可以在`.env`文件中设置以下环境变量：

- `DOUBAO_API_KEY`：豆包API密钥
- `DOUBAO_API_URL`：豆包生图API地址
- `DOUBAO_MODEL`：豆包生图模型名称
- `DOUBAO_VISION_API_URL`：豆包视觉理解API地址
- `DOUBAO_VISION_MODEL`：豆包视觉理解模型名称
- `SCREENSHOTS_DIR`：截图目录路径
- `OUTPUTS_DIR`：输出目录路径
- `LOGS_DIR`：日志目录路径

### 配置文件

也可以通过`paths.json`文件配置路径：

```json
{
  "screenshots_dir": "路径/到/Screenshots",
  "outputs_dir": "路径/到/Outputs",
  "logs_dir": "路径/到/logs"
}
```

## 提示词管理

系统使用`src/utils/prompt.py`集中管理所有提示词，包括：

- 视觉理解提示词
- 图像生成提示词
- 提示词组合模板

可以根据需要修改此文件来自定义提示词。

## 开发指南

### 项目依赖

主要依赖包括：

- streamlit：Web界面
- watchdog：文件系统监控
- Pillow：图像处理
- requests：API调用
- python-dotenv：环境变量管理
- opencv-python：图像处理
- numpy/pandas：数据处理

### 扩展功能

1. **添加新的提示词**：
   - 在`src/utils/prompt.py`中添加新的提示词

2. **支持新的API**：
   - 在`src/api/`目录下创建新的API客户端类

3. **自定义UI**：
   - 修改`src/ui/streamlit_app.py`和`src/ui/components.py`

## 故障排除

### 常见问题

1. **无法启动程序**
   - 检查Python是否正确安装
   - 确保环境变量正确设置

2. **API调用失败**
   - 检查API密钥是否正确
   - 确认网络连接正常

3. **图片未被处理**
   - 检查Screenshots目录权限
   - 查看日志文件了解详细错误信息

### 日志文件

系统日志位于`logs/app.log`，包含详细的运行信息和错误记录。

## 许可证

本项目使用MIT许可证。

## 致谢

- [豆包AI](https://www.volcengine.com/product/doubao)提供的图像生成和视觉理解API
- [Streamlit](https://streamlit.io/)提供的Web界面框架
- [Unity](https://unity.com/)游戏引擎