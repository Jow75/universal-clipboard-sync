# Universal Clipboard Sync

> **Private, fast, and secure cross-device clipboard synchronization between Windows and Android.**

Universal Clipboard Sync bridges your Windows desktop and Android phone over your local Wi-Fi network. Copy text or screenshots on your PC and paste them instantly on your phone, or send copied text and images from Android back to your PC with a single tap.

---

## ✨ Features

- **📱 Frictionless QR Code Pairing**: No more manually copying tokens across chat apps. Simply click **"Pair Phone"** in your Windows system tray, point your phone's camera at the screen, and pair in seconds.
- **🔐 Hardware & OS-Backed Security**:
  - **AES-256-GCM Authenticated Encryption**: All clipboard text and images are encrypted locally with a fresh IV and GMAC authentication tag per message.
  - **Mutual Authentication Handshake**: Clients must pass an HMAC-SHA256 challenge before receiving any clipboard frames.
  - **Windows DPAPI Storage**: Master keys are encrypted with Windows Data Protection API (`win32crypt`) in `%APPDATA%\UniversalClipboard\config.json`.
  - **Android Keystore**: Credentials are encrypted inside the hardware-backed Android Keystore.
- **🔄 Persistent Across Restarts**: Restarting Windows or Android does **not** invalidate your pairing. Reconnection happens automatically with exponential backoff and jitter.
- **📡 Smart Network Discovery**:
  - Automatically excludes virtual network adapters (WSL, Hyper-V, VirtualBox, Docker).
  - Background UDP discovery beacon (`port 8766`) automatically recovers when your PC's local DHCP IP changes.
- **🖼️ Full Image & Text Two-Way Sync**:
  - Windows to Android: Seamless background synchronization for both text and screenshots (`Win + Shift + S`).
  - Android to Windows: 1-tap sync via a persistent notification action (`[ 📋 Send to PC ]`) or an Android **Quick Settings Tile** accessible from any app.
  - Android `FileProvider` integration guarantees images can be pasted directly into WhatsApp, Slack, Gmail, and browsers without permission denials.
- **⚡ Echo-Loop Prevention**: Canonical cross-platform SHA-256 deduplication normalizes line endings (`CRLF` to `LF`) and suppresses echoing.

---

## 🚀 Quick Start Guide

### 1. Windows Installation
1. Download `UniversalClipboard.exe` from the latest **[GitHub Releases](https://github.com/universal-clipboard/universal-clipboard-sync/releases)**.
2. Run `UniversalClipboard.exe`. It launches silently into your **System Tray** (near the taskbar clock).
3. If prompted by Windows Defender Firewall, allow access on Private Networks.

### 2. Android Installation
1. Download `app-debug.apk` from the latest **GitHub Releases** on your Android phone.
2. Open the APK to install (enable "Install unknown apps" for your browser if prompted).
3. Open **Universal Clipboard** and grant **Camera** and **Notification** permissions when requested.

### 3. Pairing Your Devices
1. On Windows, right-click the **Universal Clipboard** icon in your system tray and select **"📱 Pair Phone (QR Code)"**.
2. A pairing window with a QR code and a 3-minute timer will appear.
3. On your phone, tap **"📷 Scan QR Code to Pair"**.
4. Scan the QR code displayed on your PC screen.
5. Done! Both devices are now securely paired and authenticated.

---

## 📋 How Synchronization Works

### Windows ➔ Android
Simply copy any text (`Ctrl + C`) or take a screenshot (`Win + Shift + S`) on Windows. The content is automatically encrypted, sent across the local network, and placed onto your Android clipboard.

### Android ➔ Windows
*Note on Android 10+ Privacy Protections*: Starting in Android 10, the Android OS intentionally blocks background applications from reading the system clipboard. Universal Clipboard Sync provides two frictionless 1-tap methods to send your clipboard to your PC without having to open the app:

1. **Notification Action**: Whenever text or an image is copied, pull down your notification shade and tap **`[ 📋 Send to PC ]`**.
2. **Quick Settings Tile**: Add the **"Sync to PC"** tile to your phone's Quick Settings panel. Swipe down from the top of your screen from inside *any* app and tap the tile to push your clipboard to your PC instantly.

---

## 🛠️ Architecture & Specifications

```
+-------------------------------------------------------------------+
|                        Local Wi-Fi Network                        |
|                                                                   |
|   +--------------------+                 +--------------------+   |
|   |   Windows Desktop  |                 |   Android Client   |   |
|   |  - WS Server: 8765 | <== WS (AES) == |  - WS Client       |   |
|   |  - UDP Bcn:   8766 | === UDP Bcn ==> |  - UDP Listener    |   |
|   +--------------------+                 +--------------------+   |
+-------------------------------------------------------------------+
```

- **Protocol Version**: `v=2`
- **Encryption**: AES-256-GCM (96-bit IV, 128-bit Tag)
- **Challenge-Response**: HMAC-SHA256 (32-byte nonce)
- **Message Framing**: JSON envelope with Base64 ciphertext
- **Max Payload Size**: 25 MB

For in-depth architectural and security documentation, see:
- [`docs/ENGINEERING_BASELINE.md`](file:///c:/Users/gmura/Music/Copy%20and%20Paste/docs/ENGINEERING_BASELINE.md)
- [`docs/SECURITY.md`](file:///c:/Users/gmura/Music/Copy%20and%20Paste/docs/SECURITY.md)
- [`docs/NETWORK_ARCHITECTURE.md`](file:///c:/Users/gmura/Music/Copy%20and%20Paste/docs/NETWORK_ARCHITECTURE.md)
- [`docs/TEST_REPORT.md`](file:///c:/Users/gmura/Music/Copy%20and%20Paste/docs/TEST_REPORT.md)

---

## 🧪 Developer Build & Test Instructions

### Running Python Tests
```bash
python -m pytest -v
```

### Building the Windows Executable
Requires Python 3.10+ and PyInstaller:
```bash
build_exe.bat
# Output located at: dist\UniversalClipboard.exe
```

### Building the Android APK
Requires JDK 17+ and the Android SDK:
```bash
cd android
.\gradlew.bat assembleDebug
# Output located at: android\app\build\outputs\apk\debug\app-debug.apk
```

---

## ❓ Troubleshooting & FAQ

**Q: My phone cannot connect to my PC.**
- Ensure both devices are connected to the same Wi-Fi router.
- Check Windows Defender Firewall: Ensure `UniversalClipboard.exe` is allowed to receive inbound connections on port 8765.
- If your Wi-Fi has "Client Isolation" or "Guest Mode" enabled, devices cannot communicate directly with each other. Disable client isolation in your router settings.

**Q: My PC IP address changed after restarting the router.**
- The desktop app broadcasts a lightweight UDP beacon on port `8766`. The Android app listens for this beacon and will automatically reconnect to the new IP without requiring re-pairing.

---

## 📄 License
Universal Clipboard Sync is distributed under the MIT License.
