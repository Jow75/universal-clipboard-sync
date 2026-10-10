import json
import time
import unittest
from desktop.pairing import PairingSession, QR_SESSION_TTL_SECONDS


class TestQRPairing(unittest.TestCase):
    def test_pairing_session_generation(self):
        session = PairingSession(
            ip="192.168.1.100",
            port=8765,
            server_name="Workstation",
            server_id="pc-uuid-1234",
            master_key_hex="a" * 64
        )

        self.assertFalse(session.is_expired())
        self.assertEqual(len(session.ephemeral_token), 64)
        self.assertEqual(len(session.token_bytes), 32)

        # Verify QR payload string
        payload_str = session.to_qr_payload_string()
        data = json.loads(payload_str)

        self.assertEqual(data.get("action"), "pair")
        self.assertEqual(data.get("v"), 2)
        self.assertEqual(data.get("ip"), "192.168.1.100")
        self.assertEqual(data.get("port"), 8765)
        self.assertEqual(data.get("token"), session.ephemeral_token)
        self.assertEqual(data.get("name"), "Workstation")
        self.assertEqual(data.get("id"), "pc-uuid-1234")
        self.assertTrue(data.get("exp") > time.time())

        # Verify QR PIL image generation
        img = session.generate_qr_image()
        self.assertGreater(img.width, 100)
        self.assertGreater(img.height, 100)

    def test_pairing_expiration(self):
        session = PairingSession(
            ip="192.168.1.100",
            port=8765,
            server_name="Workstation",
            server_id="pc-uuid-1234",
            master_key_hex="a" * 64
        )
        # Force expiration
        session.expires_at = int(time.time()) - 10
        self.assertTrue(session.is_expired())


if __name__ == "__main__":
    unittest.main()
