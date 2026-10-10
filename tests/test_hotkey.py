import sys
import unittest
from unittest.mock import MagicMock

# Create mocks
mock_pynput = MagicMock()
mock_keyboard = MagicMock()
mock_pynput.keyboard = mock_keyboard

# Inject into sys.modules
sys.modules['pynput'] = mock_pynput
# Also inject submodule just in case
sys.modules['pynput.keyboard'] = mock_keyboard

import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from desktop import hotkey_manager
from desktop.hotkey_manager import HotkeyManager

class TestHotkeyManager(unittest.TestCase):
    
    def test_hotkey(self):
        print(f"hotkey_manager.keyboard: {hotkey_manager.keyboard}")
        print(f"mock_keyboard: {mock_keyboard}")
        
        callback = MagicMock()
        manager = HotkeyManager(callback)
        manager.start()
        
        # Verify
        mock_keyboard.GlobalHotKeys.assert_called_once()
        
        args, _ = mock_keyboard.GlobalHotKeys.call_args
        hotkeys_dict = args[0]
        self.assertIn('<ctrl>+<shift>+c', hotkeys_dict)
        
        manager.on_activate()
        callback.assert_called_once()
        
        manager.stop()

if __name__ == "__main__":
    unittest.main()
