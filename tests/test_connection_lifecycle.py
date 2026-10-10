import asyncio
import unittest
import aiohttp
from desktop.server import SecureWebSocketServer
from desktop.protocol import compute_auth_tag, PROTOCOL_VERSION
from desktop.main import write_to_windows_clipboard


class TestConnectionLifecycle(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.master_key = b"01234567890123456789012345678901"
        self.connected_events = []
        self.disconnected_events = []

        def on_connected(dev_id, dev_name):
            self.connected_events.append((dev_id, dev_name))

        def on_disconnected(dev_id):
            self.disconnected_events.append(dev_id)

        self.server = SecureWebSocketServer(
            host='127.0.0.1',
            port=9877,
            master_key_bytes=self.master_key,
            server_id="test-srv",
            server_name="Test Server",
            on_client_connected=on_connected,
            on_client_disconnected=on_disconnected
        )
        await self.server.start()

    async def asyncTearDown(self):
        await self.server.stop()

    async def _authenticate_ws(self, ws, device_id="phone-alpha", device_name="Galaxy S24"):
        msg = await ws.receive_json(timeout=2.0)
        nonce = msg.get("nonce")
        auth_tag = compute_auth_tag(nonce, self.master_key)
        await ws.send_json({
            "v": PROTOCOL_VERSION,
            "type": "auth_response",
            "device_id": device_id,
            "device_name": device_name,
            "auth_tag": auth_tag
        })
        res = await ws.receive_json(timeout=2.0)
        return res

    async def test_duplicate_connection_superseded(self):
        """Tests that when a device reconnects with the same device_id,
        the old socket is superseded cleanly without corrupting active client count."""
        session = aiohttp.ClientSession()
        try:
            # 1. Connect first socket for phone-alpha
            ws1 = await session.ws_connect('http://127.0.0.1:9877/ws')
            res1 = await self._authenticate_ws(ws1, "phone-alpha", "Galaxy S24")
            self.assertEqual(res1.get("type"), "auth_ok")
            self.assertEqual(len(self.server.authenticated_clients), 1)
            self.assertEqual(len(self.connected_events), 1)

            # 2. Connect second socket from the SAME device (e.g. Wi-Fi reconnection)
            ws2 = await session.ws_connect('http://127.0.0.1:9877/ws')
            res2 = await self._authenticate_ws(ws2, "phone-alpha", "Galaxy S24")
            self.assertEqual(res2.get("type"), "auth_ok")

            # ws1 should receive a close frame because it was superseded by ws2
            close_msg = await ws1.receive(timeout=2.0)
            self.assertEqual(close_msg.type, aiohttp.WSMsgType.CLOSE)
            self.assertTrue(ws1.closed)
            self.assertFalse(ws2.closed)

            # Active client info should still reflect exactly 1 active client
            active_info = self.server.get_active_client_info()
            self.assertEqual(len(active_info), 1)
            self.assertEqual(active_info[0]["id"], "phone-alpha")

            # Crucial: Disconnect of ws1 must NOT have fired false on_client_disconnected
            # because ws2 is the active authoritative socket!
            self.assertEqual(len(self.disconnected_events), 0)

            # 3. Now close the active ws2 socket
            await ws2.close()
            await asyncio.sleep(0.1)

            # Now on_client_disconnected MUST fire
            self.assertEqual(len(self.disconnected_events), 1)
            self.assertEqual(self.disconnected_events[0], "phone-alpha")
            self.assertEqual(len(self.server.get_active_client_info()), 0)

        finally:
            await session.close()

    def test_windows_clipboard_write_retry(self):
        """Tests that write_to_windows_clipboard handles text writes and retries cleanly."""
        res = write_to_windows_clipboard("text", "Test clipboard retry text 12345")
        self.assertTrue(res)


if __name__ == "__main__":
    unittest.main()
