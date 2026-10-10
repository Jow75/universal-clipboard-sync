import threading
from pynput import keyboard
import logging

class HotkeyManager:
    def __init__(self, callback):
        """
        Initialize HotkeyManager.
        :param callback: Function to call when hotkey is pressed.
        """
        self.callback = callback
        self.listener = None
        self.logger = logging.getLogger(__name__)

    def start(self):
        # We use GlobalHotKeys for better handling of combinations
        # Shortcut: Ctrl + Shift + C
        self.listener = keyboard.GlobalHotKeys({
            '<ctrl>+<shift>+c': self.on_activate
        })
        self.listener.start()
        self.logger.info("Hotkey listener started (Ctrl+Shift+C)")

    def stop(self):
        if self.listener:
            self.listener.stop()
        self.logger.info("Hotkey listener stopped")

    def on_activate(self):
        self.logger.info("Hotkey activated!")
        if self.callback:
            self.callback()
