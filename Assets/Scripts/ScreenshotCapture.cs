using UnityEngine;
using System.IO;
using System;
using System.Collections.Generic;

/// <summary>
/// 简单的截图工具，可以按照摄像机视角截图并保存到指定文件夹
/// </summary>
public class ScreenshotCapture : MonoBehaviour
{
    [Tooltip("截图保存的文件夹名称")]
    public string screenshotFolderName = "Screenshots";

    [Tooltip("输出文件夹名称，用于保存生成的图片")]
    public string outputsFolderName = "Outputs";

    [Tooltip("日志文件夹名称")]
    public string logsFolderName = "logs";

    [Tooltip("配置文件名称")]
    public string configFileName = "paths.json";

    [Tooltip("截图的快捷键")]
    public KeyCode screenshotKey = KeyCode.F12;

    [Tooltip("截图分辨率倍数，值越大分辨率越高")]
    public int superSize = 1;

    [Tooltip("是否在控制台显示截图保存路径")]
    public bool showSavePathInConsole = true;

    [Tooltip("是否在启动时检查并创建所有必要的目录")]
    public bool checkDirectoriesOnStart = true;

    private string screenshotFolderPath;
    private string outputsFolderPath;
    private string logsFolderPath;
    private string configFilePath;

    void Start()
    {
        // 初始化所有必要的文件夹路径
        if (checkDirectoriesOnStart)
        {
            InitializeAllDirectories();
        }
        else
        {
            // 只初始化截图文件夹路径
            InitializeScreenshotFolder();
        }
    }

    /// <summary>
    /// 初始化所有必要的目录
    /// </summary>
    private void InitializeAllDirectories()
    {
        // 获取基础路径
        string basePath = GetBasePath();

        // 初始化所有目录
        screenshotFolderPath = Path.Combine(basePath, screenshotFolderName);
        outputsFolderPath = Path.Combine(basePath, outputsFolderName);
        logsFolderPath = Path.Combine(basePath, logsFolderName);
        configFilePath = Path.Combine(basePath, configFileName);

        // 创建所有目录
        EnsureDirectoryExists(screenshotFolderPath, "截图");
        EnsureDirectoryExists(outputsFolderPath, "输出");
        EnsureDirectoryExists(logsFolderPath, "日志");

        // 生成配置文件，保存路径信息
        GenerateConfigFile();

        Debug.Log($"所有必要的目录已初始化完成");
    }

    /// <summary>
    /// 生成配置文件，保存路径信息
    /// </summary>
    private void GenerateConfigFile()
    {
        try
        {
            // 创建路径信息对象
            PathsContainer pathsInfo = new PathsContainer
            {
                base_path = GetBasePath(),
                screenshots_dir = screenshotFolderPath,
                outputs_dir = outputsFolderPath,
                logs_dir = logsFolderPath
            };

            // 将对象转换为JSON字符串
            string json = JsonUtility.ToJson(pathsInfo, true);

            // 写入配置文件
            File.WriteAllText(configFilePath, json);

            Debug.Log($"配置文件已生成: {configFilePath}");
        }
        catch (Exception e)
        {
            Debug.LogError($"生成配置文件时出错: {e.Message}");
        }
    }

    /// <summary>
    /// 用于序列化的路径容器类
    /// </summary>
    [Serializable]
    private class PathsContainer
    {
        public string base_path;
        public string screenshots_dir;
        public string outputs_dir;
        public string logs_dir;
    }

    /// <summary>
    /// 确保目录存在，如果不存在则创建
    /// </summary>
    private void EnsureDirectoryExists(string directoryPath, string directoryType)
    {
        try
        {
            if (!Directory.Exists(directoryPath))
            {
                Directory.CreateDirectory(directoryPath);
                Debug.Log($"{directoryType}目录已创建: {directoryPath}");
            }
            else if (showSavePathInConsole)
            {
                Debug.Log($"{directoryType}目录已存在: {directoryPath}");
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"创建{directoryType}目录时出错: {e.Message}");
        }
    }

    /// <summary>
    /// 获取基础路径
    /// </summary>
    private string GetBasePath()
    {
        // 根据平台选择合适的路径
        string basePath;

        // 在编辑器中运行时
        if (Application.isEditor)
        {
            // 使用项目根目录
            basePath = Path.GetFullPath(Path.Combine(Application.dataPath, ".."));
        }
        // 在构建的应用程序中运行时
        else
        {
            // 在Windows上使用应用程序所在目录
            if (Application.platform == RuntimePlatform.WindowsPlayer)
            {
                basePath = Path.GetDirectoryName(Application.dataPath);
            }
            // 在macOS上使用应用程序所在目录
            else if (Application.platform == RuntimePlatform.OSXPlayer)
            {
                basePath = Path.GetDirectoryName(Path.GetDirectoryName(Application.dataPath));
            }
            // 在其他平台上使用持久数据路径
            else
            {
                basePath = Application.persistentDataPath;
            }
        }

        return basePath;
    }

    void Update()
    {
        // 检测按键输入
        if (Input.GetKeyDown(screenshotKey))
        {
            // 调用协程来确保在帧渲染结束后截图
            StartCoroutine(CaptureScreenshot());
        }
    }

    /// <summary>
    /// 初始化截图保存的文件夹
    /// </summary>
    private void InitializeScreenshotFolder()
    {
        // 获取基础路径
        string basePath = GetBasePath();

        // 在选定的基础路径下创建Screenshots文件夹
        screenshotFolderPath = Path.Combine(basePath, screenshotFolderName);

        // 确保目录存在
        EnsureDirectoryExists(screenshotFolderPath, "截图");
    }

    /// <summary>
    /// 捕获屏幕截图并保存到文件
    /// </summary>
    private System.Collections.IEnumerator CaptureScreenshot()
    {
        // 等待帧渲染结束，确保截图完整
        yield return new WaitForEndOfFrame();

        try
        {
            // 生成基于时间戳的唯一文件名
            string timestamp = DateTime.Now.ToString("yyyy-MM-dd_HH-mm-ss");
            string filename = $"Screenshot_{timestamp}.png";
            string filePath = Path.Combine(screenshotFolderPath, filename);

            // 捕获屏幕截图为Texture2D
            Texture2D screenTexture = ScreenCapture.CaptureScreenshotAsTexture(superSize);

            // 将Texture2D转换为PNG格式的字节数组
            byte[] bytes = screenTexture.EncodeToPNG();

            // 将字节数组写入文件
            File.WriteAllBytes(filePath, bytes);

            // 清理资源
            Destroy(screenTexture);

            if (showSavePathInConsole)
            {
                Debug.Log($"截图已保存: {filePath}");
            }
        }
        catch (Exception e)
        {
            Debug.LogError($"截图保存失败: {e.Message}");
        }
    }

    /// <summary>
    /// 获取截图文件夹路径
    /// </summary>
    public string GetScreenshotFolderPath()
    {
        return screenshotFolderPath;
    }
}
