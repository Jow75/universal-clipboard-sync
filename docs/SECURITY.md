# Security Architecture & Threat Model

## 1. Executive Summary

Universal Clipboard Sync is built with security-first design principles. Because clipboard data frequently includes highly sensitive materials (passwords, 2FA codes, authentication tokens, financial details, private correspondence, and personal photos), the communication protocol, storage layer, and pairing ceremony are hardened against passive eavesdropping, man-in-the-middle (MITM) attacks, replay attacks, resource exhaustion, and local storage exfiltration.

---

## 2. Cryptographic Architecture

### 2.1 Encryption Standard
- **Cipher**: AES-256-GCM (Galois/Counter Mode).
- **Key Length**: 256 bits (32 bytes), derived cryptographically via CSPRNG (`os.urandom(32)` on Windows, `SecureRandom` on Android).
- **IV / Nonce**: 96-bit (12-byte) unique IV generated per message frame.
- **Authentication Tag**: 128-bit (16-byte) GMAC integrity and authentication tag appended or prepended in the GCM ciphertext structure.
- **Encrypted Payload**: All clipboard content (both plain text strings and binary image byte arrays) are encrypted prior to transport.

### 2.2 Mutual Handshake & Challenge-Response Authentication
Unauthenticated WebSocket connections are strictly barred from participating in clipboard synchronization:
1. Upon connection, the server places the client in an `Unauthenticated` state and transmits an ephemeral 32-byte cryptographic challenge nonce.
2. The client must compute an HMAC-SHA256 signature over the nonce using the shared `master_key_hex`.
3. If the signature does not match or times out (5 seconds), the socket is immediately closed with code `4001` (Unauthorized).
4. No clipboard frames are transmitted or accepted on unauthenticated channels.

### 2.3 Ephemeral QR Pairing Protocol
- **No Static Token Exposure**: Long-term device keys are never placed statically in plaintext QR codes or transmitted across unencrypted media.
- **Ephemeral Session Token**: Desktop generates an ephemeral 32-byte hexadecimal session token with a 3-minute hard expiration window.
- **Single-Use Binding**: Once an Android device pairs and establishes credentials using the token, the pairing session is immediately destroyed.
- **Automatic Invalidation**: Expired or cancelled QR codes are wiped from memory.

---

## 3. Platform Secure Storage Hardening

| Platform | Old Vulnerable State | Hardened Architecture |
| :--- | :--- | :--- |
| **Windows Desktop** | Regenerated new encryption key on every boot in volatile memory; or saved in plaintext `.env` | **Windows DPAPI** (`win32crypt.CryptProtectData`): Master key is encrypted with the user's logon credentials and persisted to `%APPDATA%\UniversalClipboard\config.json`. Only processes running as the authenticated user can decrypt it. |
| **Android Client** | Plaintext `SharedPreferences` (`shared_prefs/app_prefs.xml`) readable on rooted devices or backup extractions | **AndroidKeyStore Hardware-Backed Keystore**: Master key is encrypted via `AES/GCM/NoPadding` with a hardware-backed master key generated in the Android Keystore, stored in `ucs_secure_prefs`. |

---

## 4. Threat Model & Mitigations

| Threat | Risk Level | Mitigation Implemented |
| :--- | :--- | :--- |
| **1. Rogue LAN Eavesdropping** | High | All network traffic is encrypted via AES-256-GCM. An attacker capturing LAN traffic via Wireshark sees only encrypted ciphertext frames. |
| **2. Rogue LAN Device Connection** | High | WebSocket server rejects unauthenticated peers. Handshake requires HMAC-SHA256 proof of possession of the master key. |
| **3. Replay Attacks** | Medium | Handshake uses a 32-byte random challenge nonce per session. Clipboard frames include monotonic sequence timestamps and SHA-256 content hashes. |
| **4. Denial of Service / Memory Exhaustion** | High | Strict frame limits: Max WebSocket frame size set to 25 MB (`max_msg_size = 25 * 1024 * 1024`). Payloads exceeding limits are rejected before memory allocation. |
| **5. Stolen Configuration File** | Medium | Desktop config file is encrypted with Windows DPAPI. Exfiltrating `config.json` alone does not yield the plaintext master key on another system or user account. |
| **6. Android Clip Content Injection** | Medium | All incoming clipboard payloads are authenticated with AES-GCM tags. FileProvider content URIs are generated with strictly bounded temporary read-only permissions (`FLAG_GRANT_READ_URI_PERMISSION`). |
| **7. Echo Loop / Amplification Attack** | High | Cross-platform SHA-256 deduplication normalizes text (CRLF -> LF) and records last seen hashes. Received clips are placed in suppression caches to prevent echo loops. |

---

## 5. Security Best Practices for Users
1. **Private Networks Only**: Run Universal Clipboard Sync on trusted home or corporate Wi-Fi networks. Avoid unencrypted open public Wi-Fi without a VPN.
2. **Device Pairing**: Only scan the pairing QR code from your own desktop monitor. Never share photos or screenshots of the pairing QR code.
3. **Revocation**: If a device is lost or compromised, use the Windows system tray option `📱 Pair Phone (QR Code)` or delete `%APPDATA%\UniversalClipboard\config.json` to generate a fresh master key.
