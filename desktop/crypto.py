import os
import base64
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class CryptoManager:
    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256")
        self.aesgcm = AESGCM(key)

    def encrypt(self, payload_or_type, data: str = None) -> str:
        """
        Encrypts a clipboard payload (text or image).
        Accepts either a dictionary payload or (clip_type, data).
        Returns a base64-encoded encrypted string (nonce + ciphertext + tag).
        """
        if isinstance(payload_or_type, dict):
            payload_json = json.dumps(payload_or_type)
        else:
            payload_json = json.dumps({"type": payload_or_type, "data": data})

        nonce = os.urandom(12)
        ciphertext_with_tag = self.aesgcm.encrypt(nonce, payload_json.encode('utf-8'), None)
        payload = nonce + ciphertext_with_tag
        return base64.b64encode(payload).decode('utf-8')

    def decrypt(self, encrypted_payload: str) -> dict:
        """
        Decrypts an encrypted payload.
        Returns dict: {"type": "text"|"image", "data": "..."}
        """
        try:
            payload = base64.b64decode(encrypted_payload)
            if len(payload) < 12 + 16:
                raise ValueError("Payload too short")
            nonce = payload[:12]
            ciphertext_with_tag = payload[12:]
            plaintext = self.aesgcm.decrypt(nonce, ciphertext_with_tag, None)
            return json.loads(plaintext.decode('utf-8'))
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")


def generate_key() -> str:
    return os.urandom(32).hex()


def key_from_hex(hex_key: str) -> bytes:
    return bytes.fromhex(hex_key)
