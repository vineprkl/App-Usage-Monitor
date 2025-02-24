import json
from flask import Flask, render_template, jsonify, request
import psutil
import win32gui
import win32process
import datetime
import sqlite3
import time
import config
import os
from functools import wraps

app = Flask(__name__)
DATABASE = 'app_usage.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def load_config():
    """加载配置文件"""
    default_settings = {
        'monitoring_enabled': config.MONITORING_ENABLED,
        'ignore_title_changes': config.IGNORE_TITLE_CHANGES,
        'ignored_apps': config.IGNORED_APPS,
        'custom_names': {},
        'hidden_from_web': config.HIDDEN_FROM_WEB,
        'hidden_app_display': config.HIDDEN_APP_DISPLAY
    }
    
    try:
        if os.path.exists(config.CONFIG_FILE):
            with open(config.CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved_settings = json.load(f)
                # 合并保存的设置和默认设置
                settings = default_settings.copy()
                settings.update(saved_settings)
                # 清除被隐藏应用的历史数据
                clean_hidden_apps_data(settings.get('hidden_from_web', []))
                return settings
    except Exception as e:
        print(f"加载配置文件失败: {e}")
    return default_settings

def clean_hidden_apps_data(hidden_apps):
    """清除被隐藏应用的历史数据"""
    if not hidden_apps:
        return
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 构建 SQL 查询
    placeholders = ','.join('?' * len(hidden_apps))
    cursor.execute(f"""
        DELETE FROM app_usage 
        WHERE process_name IN ({placeholders})
    """, hidden_apps)
    
    conn.commit()
    conn.close()
    print(f"已清除被隐藏应用的历史数据")

def create_table():
    """创建数据库表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            process_name TEXT,
            window_title TEXT,
            start_time TEXT,
            end_time TEXT,
            is_foreground INTEGER  -- 1 表示前台, 0 表示后台
        )
    ''')
    conn.commit()
    conn.close()

def insert_data(process_name, window_title, start_time, is_foreground):
    """插入数据到数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO app_usage (process_name, window_title, start_time, end_time, is_foreground)
        VALUES (?, ?, ?, NULL, ?)
    ''', (process_name, window_title, start_time.isoformat(), is_foreground))
    conn.commit()
    conn.close()

def update_end_time(process_name, window_title):
    """更新进程的结束时间"""
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().isoformat()
    cursor.execute('''
        UPDATE app_usage
        SET end_time = ?
        WHERE process_name = ? AND window_title = ? AND end_time IS NULL
    ''', (now, process_name, window_title))
    conn.commit()
    conn.close()

def get_display_name(process_name):
    """获取应用程序的显示名称"""
    return config.APP_DISPLAY_NAMES.get(process_name, process_name)

def get_running_applications():
    """获取当前运行的所有应用程序信息
    
    返回一个列表，每个元素包含：
    - process_name: 进程名称（可能是自定义的显示名称）
    - window_titles: 该进程的所有窗口标题
    - process_start_time: 进程启动时间
    - ignore_title_changes: 是否忽略标题变化
    """
    settings = load_config()
    app_list = []
    
    # 用于存储进程的第一个标题
    first_titles = {}
    
    for process in psutil.process_iter(['pid', 'name', 'create_time']):
        try:
            process_name = process.info['name']
            
            # 跳过被忽略或隐藏的应用
            if process_name in settings['ignored_apps'] or process_name in settings['hidden_from_web']:
                continue
                
            process_start_time = datetime.datetime.fromtimestamp(process.info['create_time']).strftime("%Y-%m-%d %H:%M:%S")
            display_name = get_display_name(process_name)

            # 获取这个进程的所有窗口标题
            def callback(hwnd, window_titles):
                if win32gui.IsWindowVisible(hwnd) and win32process.GetWindowThreadProcessId(hwnd)[1] == process.info['pid']:
                     window_title = win32gui.GetWindowText(hwnd)
                     if window_title:
                         window_titles.append(window_title)

            window_titles = []
            win32gui.EnumWindows(callback, window_titles)

            # 只记录有窗口的应用程序
            if window_titles:
                # 检查是否忽略标题变化
                ignore_title = process_name in settings['ignore_title_changes']
                
                # 如果设置了忽略标题变化
                if ignore_title:
                    # 如果是第一次遇到这个进程，保存它的第一个标题
                    if process_name not in first_titles:
                        first_titles[process_name] = display_name
                    # 使用保存的第一个标题
                    window_titles = [first_titles[process_name]]
                
                app_list.append({
                    "process_name": display_name,
                    "window_titles": window_titles,
                    "process_start_time": process_start_time,
                    "ignore_title_changes": ignore_title  # 添加标志
                })

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    return app_list

def get_foreground_window_info():
    """获取当前前台窗口的信息
    
    返回一个字典，包含：
    - process_name: 进程名称（可能是自定义的显示名称）
    - window_title: 窗口标题
    
    如果是隐藏的应用，会返回配置中设置的替代显示文本
    """
    settings = load_config()
    hwnd = win32gui.GetForegroundWindow()
    if hwnd and settings['monitoring_enabled']:
        try:
            thread_id, process_id = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(process_id)
            process_name = process.name()
            
            # 如果是被忽略的应用，返回空值
            if process_name in settings['ignored_apps']:
                return {"process_name": "None", "window_title": "None"}
            
            # 如果是隐藏的应用，返回自定义显示文本
            if process_name in settings.get('hidden_from_web', []):
                hidden_display = settings.get('hidden_app_display', config.HIDDEN_APP_DISPLAY)
                return {
                    "process_name": hidden_display.get('process_name', '其他应用'),
                    "window_title": hidden_display.get('window_title', '工作中')
                }
                
            window_title = win32gui.GetWindowText(hwnd)
            display_name = get_display_name(process_name)
            
            # 如果设置了忽略标题变化，窗口标题显示为进程名
            if process_name in settings['ignore_title_changes']:
                window_title = display_name
                
            return {"process_name": display_name, "window_title": window_title}
        except psutil.NoSuchProcess:
            return {"process_name": "Unknown", "window_title": "Unknown"}
        except Exception as e:
            print(f"获取前台窗口信息时出错: {e}")
            return {"process_name": "Error", "window_title": "Error"}
    else:
        return {"process_name": "None", "window_title": "None"}

def update_database():
    """更新数据库中的应用使用记录
    
    主要功能：
    1. 记录新启动的应用
    2. 更新已关闭应用的结束时间
    3. 处理前台应用的特殊情况
    4. 清理过期数据
    """
    settings = load_config()
    if not settings['monitoring_enabled']:
        return
        
    create_table()

    # 获取当前运行的应用和前台应用信息
    running_apps = get_running_applications()
    foreground_app = get_foreground_window_info()

    # 检查前台应用是否需要隐藏
    thread_id, process_id = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())
    try:
        foreground_process = psutil.Process(process_id)
        if foreground_process.name() in settings.get('hidden_from_web', []):
            foreground_app = {"process_name": "None", "window_title": "None"}
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

    # 获取数据库中的运行中应用列表
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT process_name, window_title FROM app_usage WHERE end_time IS NULL")
    db_running_apps = set([(row['process_name'], row['window_title']) for row in cur.fetchall()])
    conn.close()

    # 记录新启动的应用
    now = datetime.datetime.now()
    for app in running_apps:
        # 检查是否使用了自定义名称
        original_name = None
        for proc_name, custom_name in settings.get('custom_names', {}).items():
            if custom_name == app['process_name']:
                original_name = proc_name
                break
        process_name = original_name or app['process_name']
        
        # 跳过隐藏的应用
        if process_name in settings.get('hidden_from_web', []):
            continue
            
        # 设置应用的前台/后台状态
        is_foreground = 0  # 默认为后台
        if foreground_app['process_name'] == app['process_name'] and foreground_app['window_title']:
            is_foreground = 1
            
        # 记录新的窗口
        for title in app['window_titles']:
             if (app['process_name'], title) not in db_running_apps:
                insert_data(app['process_name'], title, now, is_foreground)

    # 更新已关闭应用的结束时间
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT process_name, window_title FROM app_usage WHERE end_time IS NULL")
    db_running_apps = [(row['process_name'], row['window_title']) for row in cur.fetchall()]
    conn.close()

    for process_name, window_title in db_running_apps:
        found = False
        for app in running_apps:
            for title in app['window_titles']:
                if app['process_name'] == process_name and title == window_title:
                    found = True
                    break
        if not found:
            update_end_time(process_name, window_title)

    # 处理没有窗口但在前台的特殊应用
    if foreground_app['process_name'] != "None" and not any(app['process_name'] == foreground_app['process_name'] for app in running_apps):
        # 检查是否使用了自定义名称
        original_name = None
        for proc_name, custom_name in settings.get('custom_names', {}).items():
            if custom_name == foreground_app['process_name']:
                original_name = proc_name
                break
        process_name = original_name or foreground_app['process_name']
        
        # 如果不是隐藏的应用，记录它
        if process_name not in settings.get('hidden_from_web', []):
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT process_name, window_title FROM app_usage WHERE process_name = ? and window_title = ?", 
                       (foreground_app['process_name'], foreground_app['window_title']))
            app_check = cur.fetchone()
            conn.close()
            if not app_check:
                insert_data(foreground_app['process_name'], foreground_app['window_title'], now, 1)

def cleanup_database():
    """清理数据库，删除旧数据"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cutoff_time = datetime.datetime.now() - datetime.timedelta(seconds=config.DATA_RETENTION_SECONDS)
    cutoff_time_str = cutoff_time.isoformat()

    cursor.execute("DELETE FROM app_usage WHERE start_time < ?", (cutoff_time_str,))
    conn.commit()
    conn.close()
    print("Database cleanup completed.")

def calculate_running_time(start_time_str, end_time_str):
    """计算运行时间"""
    start_time = datetime.datetime.fromisoformat(start_time_str)
    end_time = datetime.datetime.fromisoformat(end_time_str)
    running_time = end_time - start_time
    return running_time

@app.route('/')
def index():
    update_database() # 每次访问首页都更新数据库
    running_apps = get_running_applications() #然后显示
    foreground_app = get_foreground_window_info() #这个也一起显示
    return render_template('index.html', running_apps=running_apps, foreground_app=foreground_app)

@app.route('/history')
def history():
    """显示历史记录"""
    settings = load_config()
    hidden_apps = settings.get('hidden_from_web', [])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 修改SQL查询以排除被隐藏的应用
    placeholders = ','.join('?' * len(hidden_apps)) if hidden_apps else "''"
    cursor.execute(f"""
        SELECT process_name, window_title, start_time, end_time
        FROM app_usage
        WHERE end_time IS NOT NULL
        AND process_name NOT IN ({placeholders})
        ORDER BY start_time DESC
        LIMIT 100
    """, hidden_apps if hidden_apps else [])
    
    rows = cursor.fetchall()
    history_data = []
    for row in rows:
        start_time = row['start_time']
        end_time = row['end_time']
        running_time = None
        if start_time and end_time:
            running_time = calculate_running_time(start_time, end_time)
        history_data.append({
            'process_name': row['process_name'],
            'window_title': row['window_title'],
            'start_time': start_time,
            'end_time': end_time,
            'running_time': str(running_time) if running_time else "N/A"
        })
    conn.close()
    return render_template('history.html', history_data=history_data)

@app.route('/foreground')
def foreground():
     foreground_app = get_foreground_window_info()
     return jsonify(foreground_app)

@app.route('/api/data')
def get_data():
    settings = load_config()
    hidden_apps = settings.get('hidden_from_web', [])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 修改SQL查询以排除被隐藏的应用
    cursor.execute("""
        SELECT process_name, window_title, start_time, end_time 
        FROM app_usage 
        WHERE process_name NOT IN ({})
        ORDER BY start_time DESC
    """.format(','.join('?' * len(hidden_apps))), hidden_apps)
    
    rows = cursor.fetchall()
    data = []
    
    for row in rows:
        process_name, window_title, start_time, end_time = row
        display_name = settings.get('custom_names', {}).get(process_name, process_name)
        
        data.append({
            'name': display_name,
            'title': window_title,
            'start_time': start_time,
            'end_time': end_time
        })
    
    conn.close()
    return jsonify(data)

@app.route('/api/running_apps')
def get_running_apps():
    """获取运行中的应用列表的API"""
    update_database()  # 更新数据库
    running_apps = get_running_applications()
    return jsonify(running_apps)

if __name__ == '__main__':
    # 创建数据库表
    create_table()

    # 定时清理数据库 (例如每小时一次)
    import threading
    def run_cleanup():
        while True:
            cleanup_database()
            time.sleep(3600)  # 每小时清理一次

    cleanup_thread = threading.Thread(target=run_cleanup)
    cleanup_thread.daemon = True  # 设置为守护线程，主线程退出时自动退出
    cleanup_thread.start()

    # 启动Flask应用，监听所有网络接口
    app.run(host='0.0.0.0', port=5000, debug=False)