"""
Clipboard Data Manager: Gets text IN and OUT of the system clipboard.
"""
import platform
import subprocess
from .system import System

class Clipboard:
    @staticmethod
    def read_clipboard() -> str:
        """
        Read text from the system clipboard (Ctrl+C/Ctrl+V buffer).
        """
        # 1. Try Wayland (native)
        try:
            result = subprocess.run(['wl-paste'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # 2. Try X11 (native) - read from clipboard selection
        try:
            result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
            
        try:
            result = subprocess.run(['xsel', '--clipboard', '--output'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # 3. Try MacOS
        try:
            result = subprocess.run(['pbpaste'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # 4. Try Windows
        try:
            result = subprocess.run(['powershell', '-command', 'Get-Clipboard'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # 5. Fallback to Library (if installed/available)
        try:
            import pyperclip
            return pyperclip.paste()
        except ImportError:
            pass
            
        return ""

    @staticmethod
    def read_primary() -> str:
        """
        Read text from the X11 primary selection (mouse selection buffer).
        """
        # 1. Try Wayland
        try:
            result = subprocess.run(['wl-paste', '--primary'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # 2. Try X11 - read from primary selection
        try:
            result = subprocess.run(['xclip', '-selection', 'primary', '-o'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
            
        try:
            result = subprocess.run(['xsel', '--primary', '--output'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
            
        return ""

    @staticmethod
    def write_primary(text: str) -> bool:
        """
        Copy text to the X11 primary selection (for middle-click/Shift+Insert pasting).
        """
        # 1. Try Wayland
        if System.run(['wl-copy', '--primary'], text): return True
        
        # 2. Try X11 - write to primary selection
        if System.run(['xclip', '-selection', 'primary'], text): return True
        if System.run(['xsel', '--primary', '--input'], text): return True
        
        return False

    @staticmethod
    def write_clipboard(text: str) -> bool:
        """
        Copy text to the system clipboard (for Ctrl+V pasting).
        """
        # 1. Try Wayland (native)
        if System.run(['wl-copy'], text): return True
        
        # 2. Try X11 (native)
        if System.run(['xclip', '-selection', 'clipboard'], text): return True
        if System.run(['xsel', '--clipboard', '--input'], text): return True
        
        # 3. Try MacOS
        if System.run(['pbcopy'], text): return True
        
        # 4. Try Windows
        if System.run(['clip'], text): return True
        
        # 5. Fallback to Library (if installed/available)
        try:
            import pyperclip
            pyperclip.copy(text)
            return True
        except ImportError:
            pass
            
        return False

    @staticmethod
    def read() -> str:
        """
        Read from clipboard (backward compatibility).
        """
        return Clipboard.read_clipboard()

    @staticmethod  
    def write(text: str) -> bool:
        """
        Write to clipboard (backward compatibility).
        """
        return Clipboard.write_clipboard(text)
