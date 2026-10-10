import asyncio
import json
import unittest
import aiohttp
from desktop.server import SecureWebSocketServer
from desktop.protocol import compute_auth_tag, PROTOCOL_VERSION


class TestServerAuthentication(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.master_key = b"01234567890123456789012345678901"
        self.received_messages = []

        def on_receive(data):
            self.received_messages.append(data)

        self.server = SecureWebSocketServer(
            host='127.0.0.1',
            port=9876,
            master_key_bytes=self.master_key,
            server_id="test-srv",
            server_name="Test Server",
            on_receive=on_receive
        )
        await self.server.start()

    async def asyncTearDown(self):
        await self.server.stop()

    async def test_valid_handshake(self):
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect('http://127.0.0.1:9876/ws') as ws:
                # 1. Server sends challenge
                msg = await ws.receive_json(timeout=2.0)
                self.assertEqual(msg.get("type"), "auth_challenge")
                nonce = msg.get("nonce")
                self.assertTrue(bool(nonce))

                # 2. Client responds with valid HMAC
                auth_tag = compute_auth_tag(nonce, self.master_key)
                await ws.send_json({
                    "v": PROTOCOL_VERSION,
                    "type": "auth_response",
                    "device_id": "phone-1",
                    "device_name": "Pixel 9",
                    "auth_tag": auth_tag
                })

                # 3. Server sends auth_ok
                res = await ws.receive_json(timeout=2.0)
                self.assertEqual(res.get("type"), "auth_ok")
                self.assertEqual(len(self.server.authenticated_clients), 1)

                # 4. Client sends test clipboard payload
                await ws.send_str("test-encrypted-payload")
                await asyncio.sleep(0.1)
                self.assertIn("test-encrypted-payload", self.received_messages)

    async def test_invalid_handshake_rejected(self):
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect('http://127.0.0.1:9876/ws') as ws:
                msg = await ws.receive_json(timeout=2.0)
                self.assertEqual(msg.get("type"), "auth_challenge")

                # Send wrong auth tag
                await ws.send_json({
                    "v": PROTOCOL_VERSION,
                    "type": "auth_response",
                    "device_id": "attacker-phone",
                    "device_name": "Malicious Device",
                    "auth_tag": "invalid-tag-12345"
                })

                res = await ws.receive_json(timeout=2.0)
                self.assertEqual(res.get("type"), "auth_fail")
                # Connection should close
                close_msg = await ws.receive()
                self.assertEqual(close_msg.type, aiohttp.WSMsgType.CLOSE)
                self.assertEqual(len(self.server.authenticated_clients), 0)


    async def test_qr_pairing_and_key_provisioning(self):
        # Configure an active ephemeral QR pairing session
        ephemeral_qr_token = b"abcdef9876543210abcdef9876543210"
        self.server.set_active_pairing_session({
            "id": "test-qr-session",
            "token_bytes": ephemeral_qr_token,
            "exp": 9999999999
        })

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect('http://127.0.0.1:9876/ws') as ws:
                msg = await ws.receive_json(timeout=2.0)
                self.assertEqual(msg.get("type"), "auth_challenge")
                nonce = msg.get("nonce")

                # Client authenticates with ephemeral QR token
                auth_tag = compute_auth_tag(nonce, ephemeral_qr_token)
                await ws.send_json({
                    "v": PROTOCOL_VERSION,
                    "type": "auth_response",
                    "device_id": "fresh-phone",
                    "device_name": "New Phone",
                    "auth_tag": auth_tag
                })

                res = await ws.receive_json(timeout=2.0)
                self.assertEqual(res.get("type"), "auth_ok")
                # Must contain encrypted permanent master key payload
                self.assertIn("master_key_payload", res)

                # Decrypt master_key_payload using ephemeral QR token
                from desktop.crypto import CryptoManager
                client_qr_crypto = CryptoManager(ephemeral_qr_token)
                decrypted_key_obj = client_qr_crypto.decrypt(res["master_key_payload"])
                self.assertEqual(decrypted_key_obj["type"], "master_key")
                self.assertEqual(decrypted_key_obj["data"], self.master_key.hex())

                # Session should now be invalidated on server (single-use)
                self.assertIsNone(self.server.active_pairing_session)


if __name__ == "__main__":
    unittest.main()

