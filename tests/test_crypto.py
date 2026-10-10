import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from desktop.crypto import CryptoManager, generate_key, key_from_hex

def test_encryption_decryption():
    key_hex = generate_key()
    key_bytes = key_from_hex(key_hex)
    crypto = CryptoManager(key_bytes)

    clip_type = "text"
    plaintext = "Hello World! This is a test."

    # encrypt(clip_type, data) → encrypted_str
    encrypted = crypto.encrypt(clip_type, plaintext)
    print(f"Key: {key_hex}")
    print(f"Encrypted: {encrypted}")

    # decrypt(encrypted) → {type, data}
    result = crypto.decrypt(encrypted)
    print(f"Decrypted: {result}")

    assert result["type"] == clip_type
    assert result["data"] == plaintext
    print("Test Passed!")


if __name__ == "__main__":
    test_encryption_decryption()
