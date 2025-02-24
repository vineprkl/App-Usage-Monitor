import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import psutil
import win32gui
import win32process
import sys
import logging
from datetime import datetime

# 创建自定义的日志处理器
class TkinterHandler(logging.Handler):
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget
    
    def emit(self, record):
        msg = self.format(record)
        def append():
            if self.text_widget:
                try:
                    self.text_widget.configure(state='normal')
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.configure(state='disabled')
                    self.text_widget.see(tk.END)
                except:
                    pass
        if self.text_widget:
            self.text_widget.after(0, append)

# 创建自定义的stdout和stderr处理器
class LoggerWriter:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.buffer = ''
    
    def write(self, message):
        if message.strip():  # 忽略空消息
            self.logger.log(self.level, message.strip())
    
    def flush(self):
        pass

class AppMonitorControl:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("应用监控控制面板")
        self.root.geometry("800x600")
        self.root.minsize(600, 500)
        
        # 创建自定义样式
        style = ttk.Style()
        style.configure('Danger.TButton', foreground='red')
        
        # 配置文件路径
        self.config_file = 'settings.json'
        
        # 保存原始的stdout和stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # 创建日志文本框
        self.log_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=1)
        
        # 设置日志系统
        self.setup_logging()
        
        # 加载配置
        self.load_config()
        
        # 创建界面
        self.create_gui()
        
        # 定期更新应用列表
        self.update_running_apps()
        
        # 设置关闭窗口时的处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def on_closing(self):
        """窗口关闭时的处理"""
        try:
            # 恢复原始的stdout和stderr
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr
            
            # 移除所有日志处理器
            logger = logging.getLogger()
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            
            # 销毁窗口
            self.root.destroy()
            
            # 退出程序
            os._exit(0)
        except Exception as e:
            print(f"关闭窗口时出错: {e}")

    def __del__(self):
        """析构函数"""
        try:
            # 恢复原始的stdout和stderr
            if hasattr(self, 'original_stdout'):
                sys.stdout = self.original_stdout
            if hasattr(self, 'original_stderr'):
                sys.stderr = self.original_stderr
        except Exception:
            pass
    
    def setup_logging(self):
        """设置日志系统"""
        # 配置根日志记录器
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        
        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                    datefmt='%Y-%m-%d %H:%M:%S')
        
        # 添加处理器
        handler = TkinterHandler(self.log_text)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # 重定向stdout和stderr到日志系统
        sys.stdout = LoggerWriter(self.logger, logging.INFO)
        sys.stderr = LoggerWriter(self.logger, logging.ERROR)
    
    def load_config(self):
        """加载配置文件"""
        default_settings = {
            'ignore_title_changes': [],  # 忽略标题变化的应用
            'custom_names': {},          # 自定义显示名称
            'hidden_from_web': [],        # 在Web端隐藏的应用
            'hidden_app_display': {}     # 隐藏应用的显示设置
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    self.settings = default_settings.copy()
                    self.settings.update(saved_settings)
            else:
                self.settings = default_settings
                self.save_config()
        except Exception as e:
            print(f"加载配置失败: {e}")
            self.settings = default_settings
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def create_gui(self):
        """创建图形界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标签页
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 运行中的应用页面
        self.running_frame = ttk.Frame(notebook)
        notebook.add(self.running_frame, text="运行中的应用")
        self.create_running_page()
        
        # 设置页面
        self.settings_frame = ttk.Frame(notebook)
        notebook.add(self.settings_frame, text="设置")
        self.create_settings_page()
        
        # 日志页面
        self.log_frame = ttk.Frame(notebook)
        notebook.add(self.log_frame, text="日志")
        self.create_log_page()
    
    def create_running_page(self):
        """创建运行中的应用页面"""
        # 创建左右分栏
        paned = ttk.PanedWindow(self.running_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # 左侧应用列表
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=2)
        
        # 搜索框
        search_frame = ttk.Frame(left_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_apps)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # 应用列表
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.app_list = tk.Listbox(list_frame, selectmode=tk.SINGLE)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.app_list.yview)
        self.app_list.configure(yscrollcommand=scrollbar.set)
        
        self.app_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 右侧操作区
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        ttk.Label(right_frame, text="操作", font=('', 10, 'bold')).pack(pady=(0, 10))
        
        ttk.Button(right_frame, text="忽略标题变化",
                  command=lambda: self.toggle_setting('ignore_title_changes')).pack(fill=tk.X, pady=2)
        ttk.Button(right_frame, text="在Web端隐藏",
                  command=lambda: self.toggle_setting('hidden_from_web')).pack(fill=tk.X, pady=2)
        ttk.Button(right_frame, text="设置显示名称",
                  command=self.set_custom_name).pack(fill=tk.X, pady=2)
    
    def create_settings_page(self):
        """创建设置页面"""
        # 创建三个列表框架
        settings_notebook = ttk.Notebook(self.settings_frame)
        settings_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 全局操作框架
        global_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(global_frame, text="全局操作")
        
        # 添加隐藏应用显示设置
        ttk.Label(global_frame, text="隐藏应用显示设置", font=('', 12, 'bold')).pack(pady=10)
        
        hidden_display_frame = ttk.Frame(global_frame)
        hidden_display_frame.pack(fill=tk.X, padx=10)
        
        ttk.Label(hidden_display_frame, text="显示名称:").pack(pady=5)
        self.hidden_name_var = tk.StringVar(value=self.settings.get('hidden_app_display', {}).get('process_name', '其他应用'))
        hidden_name_entry = ttk.Entry(hidden_display_frame, textvariable=self.hidden_name_var)
        hidden_name_entry.pack(fill=tk.X, pady=2)
        
        ttk.Label(hidden_display_frame, text="显示标题:").pack(pady=5)
        self.hidden_title_var = tk.StringVar(value=self.settings.get('hidden_app_display', {}).get('window_title', '工作中'))
        hidden_title_entry = ttk.Entry(hidden_display_frame, textvariable=self.hidden_title_var)
        hidden_title_entry.pack(fill=tk.X, pady=2)
        
        ttk.Button(hidden_display_frame, text="保存显示设置",
                  command=self.save_hidden_display).pack(pady=10)
        
        ttk.Separator(global_frame, orient='horizontal').pack(fill=tk.X, pady=20)
        
        # 添加清空数据库按钮
        ttk.Label(global_frame, text="危险操作", font=('', 12, 'bold')).pack(pady=10)
        ttk.Button(global_frame, text="清空数据库",
                  style='Danger.TButton',
                  command=self.clear_database).pack(pady=5)
        
        # 忽略标题变化列表
        ignore_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(ignore_frame, text="忽略标题变化")
        
        self.ignore_list = tk.Listbox(ignore_frame)
        ignore_scroll = ttk.Scrollbar(ignore_frame, orient=tk.VERTICAL, command=self.ignore_list.yview)
        self.ignore_list.configure(yscrollcommand=ignore_scroll.set)
        
        self.ignore_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ignore_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(ignore_frame, text="移除",
                  command=lambda: self.remove_from_setting('ignore_title_changes')).pack(side=tk.BOTTOM, pady=5)
        
        # Web隐藏列表
        hide_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(hide_frame, text="Web隐藏")
        
        self.hide_list = tk.Listbox(hide_frame)
        hide_scroll = ttk.Scrollbar(hide_frame, orient=tk.VERTICAL, command=self.hide_list.yview)
        self.hide_list.configure(yscrollcommand=hide_scroll.set)
        
        self.hide_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        hide_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(hide_frame, text="移除",
                  command=lambda: self.remove_from_setting('hidden_from_web')).pack(side=tk.BOTTOM, pady=5)
        
        # 自定义名称列表
        name_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(name_frame, text="自定义名称")
        
        self.name_list = tk.Listbox(name_frame)
        name_scroll = ttk.Scrollbar(name_frame, orient=tk.VERTICAL, command=self.name_list.yview)
        self.name_list.configure(yscrollcommand=name_scroll.set)
        
        self.name_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        name_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(name_frame, text="移除",
                  command=self.remove_custom_name).pack(side=tk.BOTTOM, pady=5)
        
        # 更新设置列表
        self.update_settings_lists()
    
    def create_log_page(self):
        """创建日志页面"""
        # 创建日志文本框
        self.log_text = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.configure(state='disabled')
        
        # 创建按钮框架
        button_frame = ttk.Frame(self.log_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 清除日志按钮
        ttk.Button(button_frame, text="清除日志",
                  command=self.clear_log).pack(side=tk.LEFT, padx=5)
        
        # 记录初始日志消息
        logging.info("日志系统已启动")
    
    def clear_log(self):
        """清除日志内容"""
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
        logging.info("日志已清除")
    
    def update_settings_lists(self):
        """更新设置页面的所有列表"""
        # 更新忽略标题变化列表
        self.ignore_list.delete(0, tk.END)
        for app in self.settings['ignore_title_changes']:
            self.ignore_list.insert(tk.END, f"{self.get_display_name(app)} ({app})")
        
        # 更新Web隐藏列表
        self.hide_list.delete(0, tk.END)
        for app in self.settings['hidden_from_web']:
            self.hide_list.insert(tk.END, f"{self.get_display_name(app)} ({app})")
        
        # 更新自定义名称列表
        self.name_list.delete(0, tk.END)
        for proc_name, custom_name in self.settings['custom_names'].items():
            self.name_list.insert(tk.END, f"{proc_name} → {custom_name}")
    
    def get_display_name(self, process_name):
        """获取应用程序的显示名称"""
        return self.settings['custom_names'].get(process_name, process_name)
    
    def update_running_apps(self):
        """更新运行中的应用列表"""
        # 保存当前选中的项目
        selected_index = self.app_list.curselection()
        selected_item = self.app_list.get(selected_index[0]) if selected_index else None
        
        self.app_list.delete(0, tk.END)
        
        # 获取所有窗口和进程信息
        window_processes = {}
        def enum_window_callback(hwnd, window_processes):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    window_processes[pid] = window_processes.get(pid, [])
                    window_processes[pid].append(hwnd)
                except:
                    pass
        
        win32gui.EnumWindows(enum_window_callback, window_processes)
        
        # 用于存储进程及其所有窗口
        process_windows = {}
        
        # 只处理有窗口的进程
        for pid in window_processes:
            try:
                proc = psutil.Process(pid)
                process_name = proc.name()
                display_name = self.get_display_name(process_name)
                
                # 获取该进程的所有窗口标题
                titles = []
                for hwnd in window_processes[pid]:
                    title = win32gui.GetWindowText(hwnd)
                    if title:  # 只添加有标题的窗口
                        titles.append(title)
                
                # 如果有窗口标题，则添加到进程字典中
                if titles:
                    if display_name not in process_windows:
                        process_windows[display_name] = {
                            'process_name': process_name,
                            'titles': set()
                        }
                    process_windows[display_name]['titles'].update(titles)
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 将进程和窗口添加到列表中
        new_index = 0
        selected_new_index = None
        
        for display_name, info in sorted(process_windows.items()):
            # 获取进程的状态标记
            status_tags = []
            process_name = info['process_name']
            
            # 检查各种修改状态
            if process_name in self.settings.get('hidden_from_web', []):
                status_tags.append('已隐藏')
            if process_name in self.settings.get('ignore_title_changes', []):
                status_tags.append('忽略标题')
            if process_name in self.settings.get('custom_names', {}):
                status_tags.append('已改名')
            
            # 添加进程名和状态标记（作为主项）
            status_str = f" [{', '.join(status_tags)}]" if status_tags else ""
            list_item = f"▶ {display_name}{status_str}"
            self.app_list.insert(tk.END, list_item)
            
            # 如果有修改，设置蓝色
            if status_tags:
                self.app_list.itemconfig(new_index, fg='blue')
            
            # 检查是否是之前选中的项目
            if selected_item and selected_item.split('[')[0].strip() == f"▶ {display_name}":
                selected_new_index = new_index
            new_index += 1
            
            # 添加该进程的所有窗口标题（作为子项）
            for title in sorted(info['titles']):
                list_item = f"    {title}"
                self.app_list.insert(tk.END, list_item)
                if selected_item and selected_item == list_item:
                    selected_new_index = new_index
                new_index += 1
        
        # 如果找到了之前选中的项目，重新选中它
        if selected_new_index is not None:
            self.app_list.selection_clear(0, tk.END)
            self.app_list.selection_set(selected_new_index)
            self.app_list.see(selected_new_index)  # 确保选中项可见
        
        # 每5秒更新一次
        self.root.after(5000, self.update_running_apps)
    
    def filter_apps(self, *args):
        """根据搜索框内容过滤应用列表"""
        search_text = self.search_var.get().lower()
        self.update_running_apps()  # 重新获取列表
        
        if search_text:
            items_to_remove = []
            for i in range(self.app_list.size()):
                if search_text not in self.app_list.get(i).lower():
                    items_to_remove.append(i)
            
            # 从后向前删除，避免索引变化
            for i in reversed(items_to_remove):
                self.app_list.delete(i)
    
    def toggle_setting(self, setting_type):
        """切换应用的设置状态"""
        selection = self.app_list.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个应用")
            return
        
        app_info = self.app_list.get(selection[0])
        
        # 检查是否选中的是主项（进程名）
        if not app_info.startswith("    "):  # 如果不是以空格开头，说明是主项
            process_name = app_info[2:].strip()  # 去掉前面的箭头和空格
        else:
            messagebox.showwarning("提示", "请选择进程名称（箭头所在行），而不是具体的窗口标题")
            return
        
        # 获取原始进程名（如果是自定义名称）
        for proc_name, custom_name in self.settings['custom_names'].items():
            if custom_name == process_name:
                process_name = proc_name
                break
        
        if setting_type == 'ignore_title_changes':
            if process_name in self.settings['ignore_title_changes']:
                self.settings['ignore_title_changes'].remove(process_name)
            else:
                self.settings['ignore_title_changes'].append(process_name)
        elif setting_type == 'hidden_from_web':
            if process_name in self.settings['hidden_from_web']:
                self.settings['hidden_from_web'].remove(process_name)
            else:
                self.settings['hidden_from_web'].append(process_name)
        
        self.save_config()
        self.update_settings_lists()
    
    def set_custom_name(self):
        """设置应用的自定义显示名称"""
        selection = self.app_list.curselection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个应用")
            return
        
        app_info = self.app_list.get(selection[0])
        
        # 检查是否选中的是主项（进程名）
        if not app_info.startswith("    "):  # 如果不是以空格开头，说明是主项
            process_name = app_info[2:].strip()  # 去掉前面的箭头和空格
        else:
            messagebox.showwarning("提示", "请选择进程名称（箭头所在行），而不是具体的窗口标题")
            return
        
        # 获取原始进程名（如果是自定义名称）
        for proc_name, custom_name in self.settings['custom_names'].items():
            if custom_name == process_name:
                process_name = proc_name
                break
        
        dialog = tk.Toplevel(self.root)
        dialog.title("设置显示名称")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="进程名称:").pack(pady=5)
        ttk.Label(dialog, text=process_name, font=('', 9, 'bold')).pack()
        
        ttk.Label(dialog, text="显示名称:").pack(pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack(pady=5)
        
        if process_name in self.settings['custom_names']:
            name_entry.insert(0, self.settings['custom_names'][process_name])
        
        def submit():
            custom_name = name_entry.get().strip()
            if custom_name:
                self.settings['custom_names'][process_name] = custom_name
                self.save_config()
                self.update_running_apps()
                self.update_settings_lists()
            dialog.destroy()
        
        ttk.Button(dialog, text="确定", command=submit).pack(pady=10)
    
    def remove_from_setting(self, setting_type):
        """从设置列表中移除项目"""
        if setting_type == 'ignore_title_changes':
            selection = self.ignore_list.curselection()
            if selection:
                app_name = self.ignore_list.get(selection[0]).split(' (')[1].strip(')')
                self.settings['ignore_title_changes'].remove(app_name)
        elif setting_type == 'hidden_from_web':
            selection = self.hide_list.curselection()
            if selection:
                app_name = self.hide_list.get(selection[0]).split(' (')[1].strip(')')
                self.settings['hidden_from_web'].remove(app_name)
        
        self.save_config()
        self.update_settings_lists()
    
    def remove_custom_name(self):
        """移除自定义名称"""
        selection = self.name_list.curselection()
        if selection:
            proc_name = self.name_list.get(selection[0]).split(' → ')[0]
            del self.settings['custom_names'][proc_name]
            self.save_config()
            self.update_running_apps()
            self.update_settings_lists()
    
    def clear_database(self):
        """清空数据库"""
        if messagebox.askyesno("警告", "确定要清空所有历史数据吗？此操作不可恢复！"):
            try:
                import sqlite3
                conn = sqlite3.connect('app_usage.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM app_usage")
                conn.commit()
                conn.close()
                messagebox.showinfo("成功", "数据库已清空")
                logging.info("数据库已清空")
            except Exception as e:
                messagebox.showerror("错误", f"清空数据库失败: {e}")
                logging.error(f"清空数据库失败: {e}")
    
    def save_hidden_display(self):
        """保存隐藏应用的显示设置"""
        self.settings['hidden_app_display'] = {
            'process_name': self.hidden_name_var.get(),
            'window_title': self.hidden_title_var.get()
        }
        self.save_config()
        messagebox.showinfo("成功", "隐藏应用显示设置已保存")
        logging.info("隐藏应用显示设置已更新")
    
    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    app = AppMonitorControl()
    app.run() 