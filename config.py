# 数据保留设置
DATA_RETENTION_SECONDS = 7 * 24 * 60 * 60  # 历史数据保留7天

# 全局监控开关
MONITORING_ENABLED = True  # 设置为False可以暂停所有监控

# 常用应用程序的显示名称映射
# 可以在这里添加更多应用的显示名称
APP_DISPLAY_NAMES = {
    # 浏览器
    'msedge.exe': 'Microsoft Edge',
    'chrome.exe': 'Google Chrome',
    'firefox.exe': 'Firefox',
    
    # 开发工具
    'code.exe': 'Visual Studio Code',
    'idea64.exe': 'IntelliJ IDEA',
    'pycharm64.exe': 'PyCharm',
    
    # 系统工具
    'explorer.exe': 'Windows 资源管理器',
    'SearchApp.exe': 'Windows 搜索',
    'notepad.exe': '记事本',
    'powershell.exe': 'PowerShell',
    'cmd.exe': '命令提示符',
    
    # 社交和娱乐应用
    'wechat.exe': '微信',
    'qq.exe': 'QQ',
    'cloudmusic.exe': '网易云音乐',
    'steam.exe': 'Steam',
    'WeChat.exe': '微信',
    'QQ.exe': 'QQ',
}

# 应用程序监控设置
IGNORE_TITLE_CHANGES = []  # 不记录这些应用的窗口标题变化

# 完全忽略的应用列表（不会被记录）
IGNORED_APPS = []

# Web界面显示设置
HIDDEN_FROM_WEB = []  # 在Web界面中隐藏这些应用的记录

# 隐藏应用的显示替代文本
HIDDEN_APP_DISPLAY = {
    'process_name': '其他应用',  # 隐藏应用显示的进程名
    'window_title': '工作中'     # 隐藏应用显示的窗口标题
}

# 配置文件路径
import os
CONFIG_FILE = 'settings.json'  # 用户设置文件，可覆盖上述默认配置