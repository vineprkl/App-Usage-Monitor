# 应用使用监控系统

![Python Version](https://img.shields.io/badge/python-3.x-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

一个用于监控和记录 Windows 应用程序使用情况的工具，支持实时监控、数据统计和自定义显示。

## 功能特点

- 实时监控应用程序使用情况
- 记录应用程序运行时间和窗口标题
- Web界面实时查看当前运行的应用
- 历史记录查询
- 支持自定义应用显示名称
- 支持隐藏特定应用的记录
- 支持忽略窗口标题变化
- 数据本地存储，保护隐私

## 系统要求

- Windows 操作系统
- Python 3.x
- 必需的Python包：
  - flask
  - psutil
  - pywin32

## 安装说明

1. 确保已安装Python 3.x
2. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

### 启动程序

双击运行 `start.bat` 或在命令行中执行：
```bash
python start.py
```

程序会自动启动两个组件：
- 主应用（后台运行）
- 控制面板（图形界面）

### Web界面

启动后可以通过浏览器访问：
- 主页：`http://localhost:5000`
- 历史记录：`http://localhost:5000/history`

### 控制面板功能

1. 运行中的应用
   - 查看所有运行中的应用
   - 设置应用显示名称
   - 设置Web端隐藏
   - 设置忽略标题变化

2. 设置
   - 隐藏应用显示设置
   - 管理已设置的应用列表
   - 清空数据库

3. 日志
   - 查看系统运行日志
   - 清除日志记录

## 配置说明

### 应用设置

可以对每个应用程序进行以下设置：
- 自定义显示名称：修改应用在监控中显示的名称
- Web端隐藏：在Web界面中隐藏该应用的所有记录
- 忽略标题变化：只记录应用名称，忽略窗口标题的变化

### 隐私保护

- 所有数据存储在本地SQLite数据库中
- 可以设置隐藏敏感应用的记录
- 支持自定义隐藏应用的显示文本

## 文件说明

- `start.bat` - 启动脚本
- `start.py` - 程序启动器
- `app.py` - 主应用程序
- `control_panel.py` - 控制面板程序
- `config.py` - 配置文件
- `settings.json` - 用户设置文件
- `app_usage.db` - 数据库文件
- `requirements.txt` - 依赖包列表

## 注意事项

1. 首次运行时会自动创建必要的配置文件和数据库
2. 数据默认保留7天，可在`config.py`中修改
3. 关闭控制面板会自动停止所有相关程序
4. 使用Ctrl+C可以强制停止所有程序

## 常见问题

1. 如何完全清除某个应用的记录？
   - 在控制面板中设置该应用为"Web端隐藏"
   - 所有相关历史记录将被自动清除

2. 如何修改数据保留时间？
   - 在`config.py`中修改`DATA_RETENTION_SECONDS`值

3. 如何自定义应用显示？
   - 在控制面板中选择应用，点击"设置显示名称"
   - 或在`config.py`中修改`APP_DISPLAY_NAMES`字典
