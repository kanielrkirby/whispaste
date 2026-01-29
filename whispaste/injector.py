"""
Injector: Handles Input Simulation (Typing, Key Presses).
"""
import platform
import time
from .system import System
from .clipboard import Clipboard

class Injector:
    @staticmethod
    def send_paste_signal() -> bool:
        """
        Simulate paste from PRIMARY selection (X11) or clipboard (other systems).
        """
        # 1. Wayland - Shift+Insert pastes from primary
        if System.run(['wtype', '-M', 'shift', '-k', 'Insert', '-m', 'shift']): return True
        
        # 2. X11 - Shift+Insert and middle-click paste from PRIMARY selection
        if System.run(['xdotool', 'key', 'shift+Insert']): return True
        if System.run(['xdotool', 'click', '2']): return True
        
        # 3. MacOS - Cmd+V pastes from clipboard
        if System.run(['osascript', '-e', 'tell application "System Events" to keystroke "v" using command down']): return True
        
        # 4. Windows - PowerShell is often too slow for realtime input injection,
        # so we mostly rely on the user manually pasting if they don't have tools.
        return False

    @staticmethod
    def type_string(text: str) -> bool:
        """
        Simulate typing the string character by character.
        """
        # 1. Wayland
        if System.run(['wtype', '--', text]): return True
        
        # 2. Linux Daemon (ydotool)
        if System.run(['ydotool', 'type', '--', text]): return True
        
        # 3. X11
        if System.run(['xdotool', 'type', '--clearmodifiers', '--', text]): return True
        
        # 4. MacOS
        if System.run(['osascript', '-e', f'tell app "System Events" to keystroke "{text}"']): return True
        
        return False

    @staticmethod
    def insert(text: str):
        """
        Smart Insertion: Backup -> Copy to PRIMARY -> Paste -> Restore -> Fallback to Type.
        Uses X11 PRIMARY selection for proper paste behavior.
        """
        # Step 1: Backup original clipboard and primary selection
        original_clipboard = Clipboard.read_clipboard()
        original_primary = Clipboard.read_primary()
        
        # Step 2: Put transcribed text in PRIMARY selection (X11 way)
        if not Clipboard.write_primary(text):
            System.notify("Failed to access primary selection.")
            return

        # Step 2.5: Small delay to ensure selection operation completes (especially on X11)
        time.sleep(0.1)

        # Step 3: Try to trigger a paste action using PRIMARY selection
        if Injector.send_paste_signal():
            # Restore original selections after successful paste
            if original_primary:
                Clipboard.write_primary(original_primary)
            if original_clipboard:
                Clipboard.write_clipboard(original_clipboard)
            System.notify("Done!")
            return
            
        # Step 4: Fallback to typing (slower but reliable if paste fails)
        if Injector.type_string(text):
            # Restore original selections after successful typing
            if original_primary:
                Clipboard.write_primary(original_primary)
            if original_clipboard:
                Clipboard.write_clipboard(original_clipboard)
            System.notify("Typed!")
            return
            
        # Step 5: Give up on insertion, but still restore original selections
        if original_primary:
            Clipboard.write_primary(original_primary)
        if original_clipboard:
            Clipboard.write_clipboard(original_clipboard)
            System.notify("Insertion failed, selections restored")
        else:
            System.notify("Insertion failed")
