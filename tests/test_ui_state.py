import unittest
from desktop.pairing import PairingSession, DesktopConnectionWindow
from desktop.version import APP_NAME, APP_VERSION, CANONICAL_DOWNLOAD_PAGE


class TestUIState(unittest.TestCase):
    def setUp(self):
        self.session = PairingSession(
            ip="192.168.1.50",
            port=8765,
            server_name="Test PC",
            server_id="pc-uuid-99",
            master_key_hex="b" * 64
        )

    def test_version_constants(self):
        self.assertEqual(APP_NAME, "Universal Clipboard Sync")
        self.assertEqual(APP_VERSION, "1.1.0")
        self.assertIn("github.com/Jow75/universal-clipboard-sync", CANONICAL_DOWNLOAD_PAGE)

    def test_window_state_transitions(self):
        win = DesktopConnectionWindow(self.session)
        self.assertFalse(win.is_connected)

        # Post connected event
        win.post_event("client_connected", {"id": "android-42", "name": "Google Pixel 8"})
        self.assertFalse(win.event_queue.empty())

        event_type, data = win.event_queue.get()
        self.assertEqual(event_type, "client_connected")
        self.assertEqual(data["name"], "Google Pixel 8")

        # Calling set_connected
        win.set_connected("Google Pixel 8")
        self.assertTrue(win.is_connected)
        self.assertEqual(win.connected_device_name, "Google Pixel 8")
        self.assertTrue(win.session.is_completed)

        # Calling set_disconnected
        win.set_disconnected()
        self.assertFalse(win.is_connected)

    def test_session_refresh(self):
        old_token = self.session.ephemeral_token
        self.session.refresh()
        self.assertNotEqual(self.session.ephemeral_token, old_token)
        self.assertFalse(self.session.is_expired())


if __name__ == "__main__":
    unittest.main()
