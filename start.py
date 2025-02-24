import subprocess
import sys
import os
import threading
import time
import psutil
import signal

def run_app():
    """运行主应用"""
    try:
        pythonw = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
        subprocess.Popen([pythonw, 'app.py'])
        print("✓ 主应用已启动")
    except Exception as e:
        print(f"启动主应用失败: {e}")

def run_control_panel():
    """运行控制面板"""
    try:
        subprocess.Popen([sys.executable, 'control_panel.py'])
        print("✓ 控制面板已启动")
    except Exception as e:
        print(f"启动控制面板失败: {e}")

def check_process_running(process_name):
    """检查进程是否在运行"""
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] == process_name:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def stop_processes():
    """停止所有相关进程"""
    for proc in psutil.process_iter(['name', 'pid', 'cmdline']):
        try:
            if proc.info['name'] in ['python.exe', 'pythonw.exe']:
                cmdline = proc.info.get('cmdline', [])
                if any(x in cmdline for x in ['app.py', 'control_panel.py']):
                    proc.terminate()
                    proc.wait(timeout=3)  # 等待进程终止
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
            pass

def main():
    print("正在启动应用监控系统...")
    print("-" * 40)

    # 先停止可能已经在运行的实例
    stop_processes()
    time.sleep(1)  # 等待进程完全停止

    # 启动应用
    run_app()
    time.sleep(1)  # 稍等片刻，确保主应用启动
    run_control_panel()

    print("-" * 40)
    print("应用监控系统已启动！")
    print("\n按 Ctrl+C 可以停止所有程序")

    try:
        # 等待控制面板进程结束
        while True:
            time.sleep(1)
            # 检查控制面板是否还在运行
            control_panel_running = False
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    if proc.info['name'] == 'python.exe' and 'control_panel.py' in proc.info.get('cmdline', []):
                        control_panel_running = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            if not control_panel_running:
                break
    except KeyboardInterrupt:
        print("\n正在停止所有程序...")
    finally:
        stop_processes()
        print("已停止所有程序")

if __name__ == "__main__":
    main() 