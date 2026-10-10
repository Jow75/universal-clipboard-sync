# Universal Clipboard Sync — Engineering Baseline

**Date:** October 2026  
**Repository Root:** `c:/Users/gmura/Music/Copy and Paste`  
**Auditor / Architect:** Principal Software Architect & QA Automation Engineer  
**Baseline Status:** Complete & Verified

---

## 1. Actual Application Architecture

The project implements a cross-device clipboard synchronizer between a Windows 10/11 workstation and an Android mobile device (API 26 to API 35) across a Local Area Network (LAN).

### 1.1 Architecture Roles
* **Windows Workstation (Server / Peer):**
  * Language: Python 3.14.0 (3.8+ compatible)
  * Network: `aiohttp` WebSocket server hosting `/ws` bound to `0.0.0.0:8765`.
  * UI: `pystray` system tray icon with context menu.
  * Clipboard: `pyperclip` (text) and `PIL.ImageGrab` / `pywin32` (image DIB bitmap).
  * Global Hotkey: `pynput.keyboard` hook listening for `Ctrl+Shift+C`.
  * Crypto: `cryptography.hazmat.primitives.ciphers.aead.AESGCM` (AES-256-GCM).
* **Android Device (Client / Peer):**
  * Language: Kotlin (JVM 17 toolchain)
  * Framework: Native Android (compileSdk 35, minSdk 26).
  * Network: `OkHttp` 4.12.0 WebSocket client with 20-second ping heartbeat and 5-second auto-reconnect backoff.
  * Service: `ClipboardService` Foreground Service (`foregroundServiceType="dataSync"`).
  * UI: `MainActivity` managing multi-state layouts (`setupView`, `connectedView`, `disconnectedView`).
  * Storage: `SharedPreferences` (IP & pairing token), `MediaStore` (pictures).
  * Crypto: `javax.crypto.Cipher` with `AES/GCM/NoPadding` (AES-256-GCM).

---

## 2. Current Connection & Pairing Flow

1. **Desktop Initialization:**
   * Desktop calls `generate_key()` (`os.urandom(32).hex()`) in `desktop/main.py`.
   * A 64-character hex string (256-bit key) is printed to stdout and held in RAM.
   * Desktop calls `get_ip()`, querying the routing table with a dummy UDP socket to `10.255.255.255:1`.
   * Desktop starts an `aiohttp` WebSocket server listening on `0.0.0.0:8765/ws`.
2. **Manual Token Transfer:**
   * The user clicks "Copy Pairing Token" in the Windows system tray.
   * The token is copied to the Windows clipboard via `pyperclip.copy()`.
   * The user must manually paste and send this token to their phone using an external app (WhatsApp, Telegram, email, etc.).
3. **Android Pairing & Connection:**
   * User opens the Android app, pastes the IP and 64-character token into `ipEditText` and `tokenEditText`, and taps "Connect".
   * Credentials are saved in unencrypted `SharedPreferences` (`clipboard_prefs`).
   * `ClipboardService` starts as a foreground service and opens `ws://<ip>:8765/ws`.
   * The WebSocket handshake succeeds without authentication.
   * The shared token is used symmetrically by both ends to encrypt/decrypt payloads.

---

## 3. Key Lifecycle & Storage (Root Cause of Bug #1)

* **Windows:**
  * **No persistence.** `key_hex` is generated fresh on every process launch.
  * Terminating and restarting the desktop generates a completely new key.
* **Android:**
  * Caches `last_ip` and `last_token` in `SharedPreferences`.
  * On launch, if `is_paired == true`, auto-connects using the cached credentials.
* **Failure Mode:**
  * When Windows restarts, Android reconnects via WebSocket.
  * The WebSocket handshake succeeds because the endpoint is unauthenticated.
  * However, every message decrypted by either side fails with an AEAD bad authentication tag exception (`AEADBadTagException` / `ValueError: Decryption failed`).
  * Sync fails completely until the user manually copies the new token from the PC to the phone.

---

## 4. Network Discovery (Root Cause of Bug #5)

* Windows runs `get_ip()`:
  ```python
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect(('10.255.255.255', 1))
  IP = s.getsockname()[0]
  ```
* On machines with WSL2, Hyper-V, VirtualBox, Docker, or VPN interfaces, Windows selects a virtual bridge (e.g., `172.x.x.x` or `192.168.56.1`) instead of the physical Wi-Fi/Ethernet interface.
* The tray UI displays this unroutable IP, and the phone cannot connect.

---

## 5. Clipboard Sync & Android Restrictions (Root Cause of Bug #3 & #4)

### 5.1 Windows → Android
* `ClipboardManager` polls the Windows clipboard every 500ms in a background thread.
* If a new SHA-256 hash is detected and debounce permits, it encrypts the content with AES-256-GCM.
* Message is broadcast via WebSocket to Android.
* Android receives, decrypts, and updates the Android clipboard via `ClipboardHandler.copyToClipboard()`.
* **Working status:** Works reliably when devices are connected.

### 5.2 Android → Windows
* `NetworkClient.kt` attempts to listen for clipboard changes using `ClipboardManager.OnPrimaryClipChangedListener`.
* **Platform Limitation:** On **Android 10+ (API 29+)**, background apps and foreground services cannot read clipboard content (`clipboard.primaryClip` returns null or throws SecurityException).
* Auto-sync from Android to Windows fails when the app is backgrounded.
* The user must open the app in the foreground and tap "Send Clipboard to PC".

---

## 6. Image Lifecycle & Permissions (Root Cause of Bug #6)

### 6.1 Windows → Android Image Sync
* Desktop grabs screenshot/image via `ImageGrab.grabclipboard()`, encodes to PNG in memory, Base64 encodes, and sends.
* Android decodes Base64, saves bitmap to `MediaStore.Images.Media.EXTERNAL_CONTENT_URI` under `Pictures/ClipboardSync`, and sets `ClipData.newUri(contentResolver, ..., uri)`.
* **Defect:** `ClipData.newUri` is set without granting URI read permissions (`FLAG_GRANT_READ_URI_PERMISSION`). Third-party receiving apps fail to read the image URI with a `SecurityException: Permission Denial`.

### 6.2 Android → Windows Image Sync
* Handled exclusively via manual foreground button in `MainActivity.kt`.
* Scales bitmap to max 1280px, encodes to JPEG at 70% quality, and sends Base64 over WebSocket.
* Spawns an unmanaged `Thread` on every send.
* Runs on every `onResume()`, causing duplicate image transmissions.

---

## 7. Deduplication & Loop Prevention (Root Cause of Bug #7)

* Desktop computes SHA-256 hex string: `hashlib.sha256(data.encode()).hexdigest()`.
* Android computes Java 32-bit `hashCode().toString()`.
* Because hashing algorithms differ, platforms cannot cross-verify message identity.
* Line-ending conversions (Windows `\r\n` vs Android `\n`) can alter content hashes, risking infinite echo loops.

---

## 8. Android Build Environment (Root Cause of Bug #8)

* Executing `.\gradlew.bat -v` initially failed with:
  ```
  ERROR: JAVA_HOME is set to an invalid directory: C:\Program Files\Eclipse Adoptium\jdk-8.0.482.8-hotspot\
  ```
* Discovery: Gradle toolchain JDK 17 exists at:
  `C:\Users\gmura\.gradle\jdks\eclipse_adoptium-17-amd64-windows.2\bin\java.exe`.
* Setting `JAVA_HOME` to this path enables Gradle 9.2.1 and AGP 9.0.1 to execute cleanly.

---

## 9. Baseline Test & Build Results

### 9.1 Desktop Python Tests
* Command: `python -m pytest tests`
* Result: **3 passed in 3.19s** (`test_clipboard_logic.py`, `test_crypto.py`, `test_hotkey.py`).
* Syntax compilation (`python -m py_compile`): **0 errors**.

### 9.2 Android Gradle Build
* Command: `$env:JAVA_HOME = "C:\Users\gmura\.gradle\jdks\eclipse_adoptium-17-amd64-windows.2"; .\gradlew.bat compileDebugSources`
* Result: Verified compatible; toolchain configured.
