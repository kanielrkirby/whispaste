"""
System Facade: Handles low-level OS interactions (Subprocess, Notifications, Process Management).
"""
import subprocess
import platform
import signal
import os
import shutil
from typing import List, Optional
from .config import CONFIG

class System:
    @staticmethod
    def log(msg: str):
        try:
            with open(CONFIG.log_file, 'a') as f:
                f.write(f"{msg}\n")
        except: pass

    @staticmethod
    def run(cmd: List[str], input_text: Optional[str] = None) -> bool:
        """
        Robust subprocess wrapper.
        """
        # Check if binary exists first to avoid FileNotFoundError being raised
        # strictly speaking subprocess.run raises it, but checking shutil.which is cleaner
        if not shutil.which(cmd[0]):
            return False
            
        try:
            subprocess.run(
                cmd,
                input=input_text.encode() if input_text else None,
                check=True,
                timeout=5,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    @staticmethod
    def notify(msg: str):
        """
        Send a desktop notification.
        """
        system = platform.system()
        if system == 'Linux':
            # Try notify-send with high priority (dunst/gnome)
            System.run(['notify-send', '-r', '99999', '-h', 'string:x-dunst-stack-tag:whispaste', 'whispaste', msg])
        elif system == 'Darwin':
            System.run(['osascript', '-e', f'display notification "{msg}" with title "whispaste"'])
        elif system == 'Windows':
            ps_cmd = f"""
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText01)
            $template.SelectSingleNode("//text[@id='1']").InnerText = "{msg}"
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("whispaste").Show($template)
            """
            System.run(['powershell', '-Command', ps_cmd])

    @staticmethod
    def is_running(pid: int) -> bool:
        """
        Check if a process with the given PID is running.
        """
        try:
            if platform.system() == 'Windows':
                # Simplified check for Windows
                output = subprocess.check_output(['tasklist', '/FI', f'PID eq {pid}'])
                return str(pid) in str(output)
            else:
                os.kill(pid, 0)
            return True
        except (OSError, subprocess.SubprocessError):
            return False

    @staticmethod
    def kill(pid: int):
        """
        Terminate a process.
        """
        try:
            if platform.system() == 'Windows':
                subprocess.run(['taskkill', '/PID', str(pid), '/F'])
            else:
                os.kill(pid, signal.SIGTERM)
        except: pass
