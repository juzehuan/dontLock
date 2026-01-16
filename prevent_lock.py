#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
阻止电脑显示锁屏的软件
使用Python实现，支持GUI界面、任务栏托盘图标、开机自启
"""

import os
import sys
import time
import threading
import ctypes
import winreg
import webbrowser
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item

# 常量定义
APP_NAME = "防止锁屏工具"
APP_VERSION = "1.0.0"
LOG_FILE = "prevent_lock.log"

# 配置默认值
DEFAULT_INTERVAL = 60  # 默认间隔（秒）
DEFAULT_ENABLE_STARTUP = False  # 默认不开启开机自启

class PreventLockApp:
    """防止锁屏应用程序类"""

    def __init__(self):
        """初始化应用程序"""
        self.running = False
        self.interval = DEFAULT_INTERVAL
        self.enable_startup = DEFAULT_ENABLE_STARTUP
        self.thread = None
        self.tray_icon = None

        # 创建日志文件
        self.log_file = Path(LOG_FILE)
        self.log_file.touch(exist_ok=True)

        # 初始化主窗口
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} - v{APP_VERSION}")
        self.root.geometry("400x300")
        self.root.resizable(False, False)

        # 设置窗口图标
        self.set_window_icon()

        # 创建GUI界面
        self.create_gui()

        # 初始化系统托盘图标
        self.init_tray_icon()

        # 初始化开机自启设置
        self.check_startup_status()

        # 记录启动日志
        self.log(f"{APP_NAME} v{APP_VERSION} 启动")

    def set_window_icon(self):
        """设置窗口图标"""
        try:
            # 创建一个简单的图标
            icon = Image.new('RGB', (16, 16), color='blue')
            draw = ImageDraw.Draw(icon)
            draw.rectangle([4, 4, 12, 12], fill='white')

            # 转换为tkinter可用的图标
            photo = ImageTk.PhotoImage(icon)
            self.root.iconphoto(True, photo)
        except Exception as e:
            self.log(f"设置窗口图标失败: {e}")

    def create_gui(self):
        """创建GUI界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text=APP_NAME, font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # 状态显示
        self.status_var = tk.StringVar(value="未运行")
        self.status_color = tk.StringVar(value="red")

        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)

        ttk.Label(status_frame, text="当前状态:", width=10).pack(side=tk.LEFT)
        status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground=self.status_color.get(), font=("Arial", 10, "bold"))
        status_label.pack(side=tk.LEFT, padx=5)

        # 间隔设置
        interval_frame = ttk.Frame(main_frame)
        interval_frame.pack(fill=tk.X, pady=10)

        ttk.Label(interval_frame, text="活动间隔:", width=10).pack(side=tk.LEFT)
        self.interval_var = tk.StringVar(value=str(DEFAULT_INTERVAL))
        interval_entry = ttk.Entry(interval_frame, textvariable=self.interval_var, width=10)
        interval_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(interval_frame, text="秒").pack(side=tk.LEFT)

        # 开机自启设置
        startup_frame = ttk.Frame(main_frame)
        startup_frame.pack(fill=tk.X, pady=10)

        self.startup_var = tk.BooleanVar(value=DEFAULT_ENABLE_STARTUP)
        startup_check = ttk.Checkbutton(startup_frame, text="开机自启", variable=self.startup_var, command=self.toggle_startup)
        startup_check.pack(anchor=tk.W)

        # 日志显示
        log_label = ttk.Label(main_frame, text="运行日志:", font=("Arial", 10, "bold"))
        log_label.pack(anchor=tk.W, pady=10)

        log_frame = ttk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, height=8, width=40, font=("Courier New", 9))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        # 按钮组
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)

        self.start_btn = ttk.Button(button_frame, text="开始", command=self.start_prevent_lock)
        self.start_btn.pack(side=tk.LEFT, padx=5, expand=True)

        self.stop_btn = ttk.Button(button_frame, text="停止", command=self.stop_prevent_lock, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5, expand=True)

        # 更新日志显示
        self.update_log_display()

    def init_tray_icon(self):
        """初始化系统托盘图标"""
        try:
            # 创建一个简单的图标
            icon = Image.new('RGB', (64, 64), color='blue')
            draw = ImageDraw.Draw(icon)
            draw.rectangle([16, 16, 48, 48], fill='white')

            # 创建菜单
            menu = (
                item('显示主窗口', self.show_window),
                item('开始', self.start_prevent_lock_tray),
                item('停止', self.stop_prevent_lock_tray),
                item('退出', self.exit_app)
            )

            # 创建托盘图标
            self.tray_icon = pystray.Icon(APP_NAME, icon, APP_NAME, menu)

            # 启动托盘图标线程
            self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()
        except Exception as e:
            self.log(f"初始化托盘图标失败: {e}")

    def prevent_lock(self):
        """防止锁屏的核心函数"""
        while self.running:
            try:
                # 调用Windows API防止锁屏
                # ES_CONTINUOUS = 0x80000000 - 持续设置
                # ES_SYSTEM_REQUIRED = 0x00000001 - 防止系统睡眠
                # ES_DISPLAY_REQUIRED = 0x00000002 - 防止显示器关闭
                # ES_AWAYMODE_REQUIRED = 0x00000040 - 防止系统进入离开模式（适用于媒体播放）
                result = ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001 | 0x00000002 | 0x00000040)
                if result == 0:
                    error_code = ctypes.GetLastError()
                    self.log(f"SetThreadExecutionState 失败，错误码: {error_code}")
                else:
                    self.log("已重置系统锁屏计时器")
                time.sleep(self.interval)
            except Exception as e:
                self.log(f"防止锁屏出错: {e}")
                time.sleep(5)

    def start_prevent_lock(self):
        """开始防止锁屏"""
        try:
            # 获取并验证间隔时间
            interval = int(self.interval_var.get())
            if interval < 10:
                messagebox.showerror("错误", "间隔时间不能小于10秒")
                return
            self.interval = interval

            if not self.running:
                self.running = True
                self.thread = threading.Thread(target=self.prevent_lock, daemon=True)
                self.thread.start()

                self.status_var.set("运行中")
                self.status_color.set("green")
                self.start_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.NORMAL)

                self.log(f"开始防止锁屏，间隔: {self.interval}秒")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")

    def stop_prevent_lock(self):
        """停止防止锁屏"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join(timeout=1)

            # 恢复系统默认设置
            # 只设置 ES_CONTINUOUS 表示恢复默认行为
            result = ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
            if result == 0:
                error_code = ctypes.GetLastError()
                self.log(f"恢复系统默认设置失败，错误码: {error_code}")
            else:
                self.log("已恢复系统默认设置")

            self.status_var.set("已停止")
            self.status_color.set("red")
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)

            self.log("已停止防止锁屏")

    def start_prevent_lock_tray(self):
        """从托盘菜单开始防止锁屏"""
        self.start_prevent_lock()

    def stop_prevent_lock_tray(self):
        """从托盘菜单停止防止锁屏"""
        self.stop_prevent_lock()

    def check_startup_status(self):
        """检查开机自启状态"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Run",
                               0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            winreg.CloseKey(key)

            self.enable_startup = True
            self.startup_var.set(True)
            self.log("开机自启已开启")
        except FileNotFoundError:
            self.enable_startup = False
            self.startup_var.set(False)
        except Exception as e:
            self.log(f"检查开机自启状态失败: {e}")

    def toggle_startup(self):
        """切换开机自启状态"""
        self.enable_startup = self.startup_var.get()

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Run",
                               0, winreg.KEY_SET_VALUE)

            if self.enable_startup:
                # 获取当前可执行文件路径
                if getattr(sys, 'frozen', False):
                    exe_path = sys.executable
                else:
                    exe_path = sys.argv[0]

                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
                self.log("已开启开机自启")
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                    self.log("已关闭开机自启")
                except FileNotFoundError:
                    pass

            winreg.CloseKey(key)
        except Exception as e:
            self.log(f"修改开机自启状态失败: {e}")
            messagebox.showerror("错误", f"修改开机自启状态失败: {e}")

    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        # 写入日志文件
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

        # 更新GUI日志显示
        self.update_log_display()

    def update_log_display(self):
        """更新日志显示"""
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # 只显示最后10行
            recent_lines = lines[-10:]

            self.log_text.delete("1.0", tk.END)
            self.log_text.insert(tk.END, "".join(recent_lines))
            self.log_text.see(tk.END)
        except Exception as e:
            self.log_text.insert(tk.END, f"读取日志失败: {e}\n")

    def show_window(self):
        """显示主窗口"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide_window(self):
        """隐藏主窗口"""
        self.root.withdraw()

    def exit_app(self):
        """退出应用程序"""
        # 停止防止锁屏
        self.stop_prevent_lock()

        # 停止托盘图标
        if self.tray_icon:
            self.tray_icon.stop()

        # 记录退出日志
        self.log(f"{APP_NAME} 退出")

        # 退出应用
        self.root.destroy()
        sys.exit(0)

    def on_closing(self):
        """窗口关闭事件处理"""
        self.hide_window()

    def run(self):
        """运行应用程序"""
        # 处理窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 初始隐藏窗口，只显示托盘图标
        self.hide_window()

        # 自动开始防止锁屏功能
        self.log("软件启动，自动开始防止锁屏功能")
        # 设置默认间隔为60秒
        self.interval = DEFAULT_INTERVAL
        self.interval_var.set(str(DEFAULT_INTERVAL))
        # 开始防止锁屏
        self.running = True
        self.thread = threading.Thread(target=self.prevent_lock, daemon=True)
        self.thread.start()

        self.status_var.set("运行中")
        self.status_color.set("green")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        # 运行主循环
        self.root.mainloop()

# 主程序入口
if __name__ == "__main__":
    try:
        # 导入所需库
        from PIL import Image, ImageDraw, ImageTk
        import pystray

        # 创建并运行应用
        app = PreventLockApp()
        app.run()
    except ImportError as e:
        print(f"缺少依赖库: {e}")
        print("请安装所需依赖: pip install pillow pystray pyautogui")
        input("按回车键退出...")
    except Exception as e:
        print(f"应用程序出错: {e}")
        input("按回车键退出...")
