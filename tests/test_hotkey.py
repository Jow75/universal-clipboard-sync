import unittest
from unittest.mock import MagicMock, patch
from desktop.hotkey_manager import HotkeyManager


class TestHotkeyManager(unittest.TestCase):
    @patch('desktop.hotkey_manager.keyboard.GlobalHotKeys')
    def test_hotkey(self, mock_global_hotkeys):
        mock_instance = MagicMock()
        mock_global_hotkeys.return_value = mock_instance

        callback = MagicMock()
        manager = HotkeyManager(callback)
        manager.start()

        # Verify GlobalHotKeys was instantiated with the right shortcut
        mock_global_hotkeys.assert_called_once()
        args, _ = mock_global_hotkeys.call_args
        hotkeys_dict = args[0]
        self.assertIn('<ctrl>+<shift>+c', hotkeys_dict)
        mock_instance.start.assert_called_once()

        # Verify callback execution
        manager.on_activate()
        callback.assert_called_once()

        manager.stop()
        mock_instance.stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()
