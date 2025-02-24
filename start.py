import subprocess
import sys
import os
import threading
import time
import psutil
import signal

def run_app():
    """启动主应用程序
    
    使用pythonw.exe在后台运行app.py，不显示控制台窗口
    """
    try:
        pythonw = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
        subprocess.Popen([pythonw, 'app.py'])
        print("✓ 主应用已启动")
    except Exception as e:
        print(f"启动主应用失败: {e}")

def run_control_panel():
    """启动控制面板程序
    
    使用python.exe运行control_panel.py，显示GUI界面
    """
    try:
        subprocess.Popen([sys.executable, 'control_panel.py'])
        print("✓ 控制面板已启动")
    except Exception as e:
        print(f"启动控制面板失败: {e}")

def check_process_running(process_name):
    """检查指定名称的进程是否在运行
    
    Args:
        process_name: 进程的可执行文件名称
        
    Returns:
        bool: 进程是否正在运行
    """
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] == process_name:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def stop_processes():
    """停止所有相关的应用进程
    
    查找并终止所有运行中的app.py和control_panel.py进程
    包括使用python.exe和pythonw.exe启动的进程
    """
    for proc in psutil.process_iter(['name', 'pid', 'cmdline']):
        try:
            if proc.info['name'] in ['python.exe', 'pythonw.exe']:
                cmdline = proc.info.get('cmdline', [])
                if any(x in cmdline for x in ['app.py', 'control_panel.py']):
                    proc.terminate()
                    proc.wait(timeout=3)  # 等待进程完全终止
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            pass

def main():
    """程序主入口
    
    执行启动流程：
    1. 停止已运行的实例
    2. 启动主应用和控制面板
    3. 监控控制面板的运行状态
    4. 处理程序退出
    """
    print("正在启动应用监控系统...")
    print("-" * 40)

    # 确保没有旧实例在运行
    stop_processes()
    time.sleep(1)  # 等待进程完全停止

    # 按顺序启动组件
    run_app()
    time.sleep(1)  # 确保主应用启动完成
    run_control_panel()

    print("-" * 40)
    print("应用监控系统已启动！")
    print("\n按 Ctrl+C 可以停止所有程序")

    try:
        # 持续监控控制面板的状态
        while True:
            time.sleep(1)
            control_panel_running = False
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    if proc.info['name'] == 'python.exe' and 'control_panel.py' in proc.info.get('cmdline', []):
                        control_panel_running = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            # 如果控制面板已关闭，退出程序
            if not control_panel_running:
                break
    except KeyboardInterrupt:
        print("\n正在停止所有程序...")
    finally:
        stop_processes()
        print("已停止所有程序")

if __name__ == "__main__":
    main() 