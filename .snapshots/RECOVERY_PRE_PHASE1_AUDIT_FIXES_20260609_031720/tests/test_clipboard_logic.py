import sys
import os
import time
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from desktop.clipboard_manager import ClipboardManager


class TestClipboardManager(unittest.TestCase):

    def test_logic(self):
        callback_mock = MagicMock()
        manager = ClipboardManager(callback_mock)
        manager.debounce_time = 0.0  # Disable debounce for this test

        # Start manager
        with patch('desktop.clipboard_manager.pyperclip.paste') as mock_paste:
            mock_paste.return_value = "Hello"

            manager.start()
            # Wait for thread to pick up
            time.sleep(1.0)

            # Callback is called with (clip_type, clip_data)
            callback_mock.assert_called_with("text", "Hello")
            callback_mock.reset_mock()

            # Wait another cycle, same text — should NOT call callback (dedupe)
            time.sleep(1.0)
            callback_mock.assert_not_called()

            # Change text — should fire again
            mock_paste.return_value = "World"
            time.sleep(1.0)
            callback_mock.assert_called_with("text", "World")

            manager.stop()


if __name__ == "__main__":
    unittest.main()
