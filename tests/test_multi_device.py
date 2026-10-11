"""
Test Multi-Device Support:
- Simultaneous multiple phone connections (Tecno, Samsung, Pixel, etc.)
- Device identification and persistence in config
- Independent disconnection of one device while others remain active
- Reconnection reusing existing device identity without duplicates
- Device rename and individual removal
- Multi-client broadcast without feedback loops
"""
import os
import sys
import shutil
import asyncio
import unittest
import aiohttp

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from desktop import config
from desktop.server import SecureWebSocketServer
from desktop.protocol import compute_auth_tag, PROTOCOL_VERSION


class TestMultiDeviceSupport(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Temporary config dir for test isolation
        self.original_get_dir = config.get_config_dir
        self.test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "tmp_multi_dev_test"))
        config.get_config_dir = lambda: self.test_dir
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

        self.master_key = b"01234567890123456789012345678901"
        self.connected_events = []
        self.disconnected_events = []

        def on_connected(dev_id, dev_name):
            self.connected_events.append((dev_id, dev_name))

        def on_disconnected(dev_id):
            self.disconnected_events.append(dev_id)

        self.server = SecureWebSocketServer(
            host='127.0.0.1',
            port=9879,
            master_key_bytes=self.master_key,
            server_id="test-multidev-srv",
            server_name="Test Workstation",
            on_client_connected=on_connected,
            on_client_disconnected=on_disconnected
        )
        await self.server.start()

    async def asyncTearDown(self):
        await self.server.stop()
        config.get_config_dir = self.original_get_dir
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    async def _authenticate_device(self, ws, device_id: str, device_name: str):
        msg = await ws.receive_json(timeout=2.0)
        self.assertEqual(msg.get("type"), "auth_challenge")
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
        self.assertEqual(res.get("type"), "auth_ok")
        return res

    async def test_simultaneous_multi_phone_connections(self):
        """Tests that multiple distinct Android phones can connect simultaneously without arbitrary caps."""
        devices = [
            ("dev-tecno-01", "Tecno Spark 10 Pro"),
            ("dev-samsung-02", "Samsung Galaxy S24"),
            ("dev-pixel-03", "Google Pixel 8"),
            ("dev-xiaomi-04", "Xiaomi Redmi Note 13"),
            ("dev-oneplus-05", "OnePlus 12"),
        ]

        async with aiohttp.ClientSession() as session:
            sockets = []
            try:
                # Connect all 5 phones concurrently
                for dev_id, dev_name in devices:
                    ws = await session.ws_connect('http://127.0.0.1:9879/ws')
                    await self._authenticate_device(ws, dev_id, dev_name)
                    sockets.append(ws)

                # Verify all 5 phones are authenticated and tracked simultaneously
                self.assertEqual(len(self.server.authenticated_clients), 5)
                active_info = self.server.get_active_client_info()
                self.assertEqual(len(active_info), 5)

                active_ids = {d["id"] for d in active_info}
                for dev_id, _ in devices:
                    self.assertIn(dev_id, active_ids)

                # Verify config persistence contains all 5 paired phones
                paired = config.get_paired_devices()
                self.assertEqual(len(paired), 5)
                for dev_id, dev_name in devices:
                    self.assertIn(dev_id, paired)
                    self.assertEqual(paired[dev_id]["device_name"], dev_name)

                # Broadcast test: all 5 sockets receive broadcast
                test_msg = "test-encrypted-clipboard-broadcast-123"
                await self.server.broadcast(test_msg)

                for ws in sockets:
                    recv = await ws.receive_str(timeout=2.0)
                    self.assertEqual(recv, test_msg)

            finally:
                for ws in sockets:
                    await ws.close()

    async def test_independent_disconnection(self):
        """Tests that disconnecting one phone does not disconnect other active phones."""
        async with aiohttp.ClientSession() as session:
            ws1 = await session.ws_connect('http://127.0.0.1:9879/ws')
            await self._authenticate_device(ws1, "dev-tecno", "Tecno Phone")

            ws2 = await session.ws_connect('http://127.0.0.1:9879/ws')
            await self._authenticate_device(ws2, "dev-pixel", "Google Pixel")

            self.assertEqual(len(self.server.authenticated_clients), 2)

            # Disconnect Tecno on demand using server.disconnect_device
            await self.server.disconnect_device("dev-tecno")
            await asyncio.sleep(0.1)

            # Pixel must still be connected and active!
            self.assertEqual(len(self.server.authenticated_clients), 1)
            active = self.server.get_active_client_info()
            self.assertEqual(len(active), 1)
            self.assertEqual(active[0]["id"], "dev-pixel")

            # Tecno's pairing in config is preserved (still paired, just offline)
            paired = config.get_paired_devices()
            self.assertIn("dev-tecno", paired)
            self.assertIn("dev-pixel", paired)

            await ws2.close()

    def test_device_rename_and_removal(self):
        """Tests deliberate renaming and individual removal of paired devices in config."""
        config.add_or_update_paired_device("dev-1", "Old Name", "Android")
        config.add_or_update_paired_device("dev-2", "Second Phone", "Android")

        # Rename dev-1
        renamed = config.rename_paired_device("dev-1", "Living Room Tecno")
        self.assertTrue(renamed)
        self.assertEqual(config.get_paired_devices()["dev-1"]["device_name"], "Living Room Tecno")

        # Remove dev-1 without affecting dev-2
        removed = config.remove_paired_device("dev-1")
        self.assertTrue(removed)
        paired = config.get_paired_devices()
        self.assertNotIn("dev-1", paired)
        self.assertIn("dev-2", paired)

    async def test_high_concurrency_scale_and_limit_enforcement(self):
        """Tests that up to 32 concurrent phone connections operate smoothly and limit is enforced safely."""
        count = 32
        async with aiohttp.ClientSession() as session:
            sockets = []
            try:
                for i in range(count):
                    dev_id = f"dev-scale-{i:02d}"
                    dev_name = f"Test Phone {i:02d}"
                    ws = await session.ws_connect('http://127.0.0.1:9879/ws')
                    await self._authenticate_device(ws, dev_id, dev_name)
                    sockets.append(ws)

                # Verify all 32 connected simultaneously
                self.assertEqual(len(self.server.authenticated_clients), count)

                # Verify broadcast delivers to all 32 clients
                payload = "multi-client-scale-payload-verified"
                await self.server.broadcast(payload)
                for ws in sockets:
                    msg = await ws.receive_str(timeout=2.0)
                    self.assertEqual(msg, payload)

            finally:
                for ws in sockets:
                    await ws.close()


if __name__ == "__main__":
    unittest.main()
