# Universal Clipboard Sync — Privacy Policy & Data Handling

Universal Clipboard Sync is designed with absolute user privacy as a foundational principle. Because clipboard data frequently includes sensitive credentials, private messages, personal identifiers, and financial data, this document explains exactly what data is handled, where it travels, and how it is secured.

---

## 1. What Data is Synchronized?
- **Text & URLs**: Standard unicode text copied on either Windows or Android.
- **Images**: PNG, JPEG, and bitmap images copied to the system clipboard.
- **Excluded Data**: Non-clipboard user data (keystrokes outside copied selections, typed passwords, location data, contacts, browsing history, and camera video) are **never** read, collected, or transmitted.

---

## 2. Where Does Clipboard Data Travel?
- **Local Wi-Fi Only**: All clipboard synchronization occurs **strictly peer-to-peer over your local area network (LAN / Wi-Fi)** directly between your Windows PC and your Android phone.
- **No Third-Party Servers**: No clipboard content, metadata, or telemetry is ever sent to Google, Microsoft, GitHub, or any third-party cloud server.
- **AES-256-GCM Encryption**: All data transmitted between your devices is encrypted in transit using an ephemeral 96-bit IV, 256-bit AES-GCM cipher, and 128-bit integrity tag. Even on a compromised Wi-Fi network, eavesdroppers see only encrypted binary ciphertext.

---

## 3. What Data is Stored Locally?
- **Windows PC**:
  - Encrypted Master Key: Stored in `%APPDATA%\UniversalClipboard\config.json`, protected by Windows Data Protection API (DPAPI). Only your logged-in Windows account can decrypt it.
  - Port & network settings (Plaintext).
  - Volatile suppression cache (in memory only, storing SHA-256 hashes of recent clips to prevent infinite copy loops). Plaintext clipboard contents are **not** written to disk.
- **Android Phone**:
  - Encrypted Master Key: Stored in `ucs_secure_prefs`, protected by the hardware-backed Android Keystore.
  - Bounded pending clipboard buffer: Up to 1 single pending text copy (held in memory for at most 60 seconds if offline, immediately discarded if disconnected or superseded).

---

## 4. How Long is Clipboard Data Retained?
- **Zero Persistent History**: Universal Clipboard Sync does **not** maintain a historical clipboard database or history log on disk.
- Once text or an image is delivered and applied to the destination system clipboard, it is purged from application transport buffers.
- Log files (`universal_clipboard.log`) strictly log connection lifecycle events (e.g. `Client connected`, `Sync completed`) and **never write clipboard contents or encryption keys**.

---

## 5. What Does the Pairing QR Code Contain?
- The Windows pairing QR code contains:
  ```json
  {"action": "pair", "sid": "<session_id>", "token": "<32_byte_token>", "exp": <epoch_timestamp>}
  ```
- **Temporary Only**: The QR token is ephemeral with a 3-minute hard expiration. It is single-use and invalidates immediately after the first successful handshake.
- It does **not** contain your permanent master key or any clipboard data.

---

## 6. What Permissions are Required?
- **Android**:
  - `INTERNET` & `ACCESS_NETWORK_STATE`: Required to connect to your PC's local WebSocket port.
  - `FOREGROUND_SERVICE` & `FOREGROUND_SERVICE_DATA_SYNC`: Required to keep the local sync connection alive while your screen is locked.
  - `POST_NOTIFICATIONS`: Required on Android 13+ to display the foreground sync status and the `[ 📋 Send to PC ]` quick action.
  - `CAMERA`: Required solely to scan the pairing QR code. The camera is active only during the scanning screen and images are never stored or uploaded.
  - `ACCESSIBILITY_SERVICE` (Optional): Required only if you choose the "Zero-Tap Seamless Sync" mode to detect copy events across apps.
- **Windows**:
  - Local network port binding (`8765` TCP for WebSockets, `8766` UDP for discovery).

---

## 7. How to Disconnect and Remove Pairing
- **On Windows**: Open the Status Window, click **Unpair Device**, or delete `%APPDATA%\UniversalClipboard\config.json`.
- **On Android**: In the app menu, tap **Unpair / Reset**. This immediately purges the hardware Keystore master key from `ucs_secure_prefs`.
