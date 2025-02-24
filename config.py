# 数据保留时间（秒）
DATA_RETENTION_SECONDS = 7 * 24 * 60 * 60  # 7天

# 全局开关
MONITORING_ENABLED = True

# 应用程序显示名称映射
APP_DISPLAY_NAMES = {
    'msedge.exe': 'Microsoft Edge',
    'chrome.exe': 'Google Chrome',
    'firefox.exe': 'Firefox',
    'code.exe': 'Visual Studio Code',
    'explorer.exe': 'Windows 资源管理器',
    'SearchApp.exe': 'Windows 搜索',
    'notepad.exe': '记事本',
    'powershell.exe': 'PowerShell',
    'cmd.exe': '命令提示符',
    'idea64.exe': 'IntelliJ IDEA',
    'pycharm64.exe': 'PyCharm',
    'wechat.exe': '微信',
    'qq.exe': 'QQ',
    'cloudmusic.exe': '网易云音乐',
    'steam.exe': 'Steam',
    'WeChat.exe': '微信',
    'QQ.exe': 'QQ',
}

# 忽略标题变化的应用列表
IGNORE_TITLE_CHANGES = []

# 完全忽略的应用列表
IGNORED_APPS = []

# 在web界面隐藏的应用列表
HIDDEN_FROM_WEB = []

# 隐藏应用的前台显示设置
HIDDEN_APP_DISPLAY = {
    'process_name': '其他应用',  # 隐藏应用在前台时显示的进程名
    'window_title': '工作中'    # 隐藏应用在前台时显示的窗口标题
}

# 配置文件路径
import os
CONFIG_FILE = 'settings.json'