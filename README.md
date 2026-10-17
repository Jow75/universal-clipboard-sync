# Universal Clipboard Sync

> **Private, fast, and secure cross-device clipboard synchronization between Windows and Android.**

Universal Clipboard Sync bridges your Windows desktop and Android phone over your local Wi-Fi network. Copy text or screenshots on your PC and paste them instantly on your phone, or send copied text and images from Android back to your PC with zero friction.

**Official Website**: [https://universal-clipboard.netlify.app/](https://universal-clipboard.netlify.app/)

[![Website](https://img.shields.io/badge/Website-universal--clipboard.netlify.app-00C7B7.svg)](https://universal-clipboard.netlify.app/)
[![Release](https://img.shields.io/badge/Release-v1.1.0-blue.svg)](https://github.com/Jow75/universal-clipboard-sync/releases/latest)
[![Platform Windows](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6.svg)](https://github.com/Jow75/universal-clipboard-sync/releases/latest)
[![Platform Android](https://img.shields.io/badge/Platform-Android%208.0%2B%20(API%2026--35)-3DDC84.svg)](https://github.com/Jow75/universal-clipboard-sync/releases/latest)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📥 Downloads (v1.1.0)

| Package | Format | Size | Description | Download Link |
| :--- | :--- | :--- | :--- | :--- |
| **Windows Setup** | `.exe` (Installer) | ~44 MB | Recommended for Windows 10 & 11. Includes Start Menu & Desktop shortcuts | [Download Setup](https://github.com/Jow75/universal-clipboard-sync/releases/download/v1.1.0/UniversalClipboard-Setup-1.1.0.exe) |
| **Windows Portable** | `.exe` (Standalone) | ~47 MB | Single-file portable executable, runs without installation | [Download Portable](https://github.com/Jow75/universal-clipboard-sync/releases/download/v1.1.0/UniversalClipboard-Portable-1.1.0.exe) |
| **Android App** | `.apk` (v2 Signed) | ~5.7 MB | For Android phones & tablets (Android 8.0 to Android 15) | [Download APK](https://github.com/Jow75/universal-clipboard-sync/releases/download/v1.1.0/UniversalClipboard-Android-1.1.0.apk) |

### 📱 Scan to Download Android APK

Scan this official download QR code with your phone camera to download the latest release:

![Download Universal Clipboard Sync](docs/assets/download_qr.png)

*Direct Link:* [https://github.com/Jow75/universal-clipboard-sync/releases/latest](https://github.com/Jow75/universal-clipboard-sync/releases/latest)

> **Local Network Download**: When the Windows application is running, you can also download the Android APK directly over your home Wi-Fi at `http://<YOUR_PC_IP>:8765/download` without needing internet access!

---

## 🔒 Verification & Authenticode Code Signing

Universal Clipboard Sync Windows executables are digitally stamped with **BAZIQHUE** metadata and signed with SHA-256 Authenticode. Users can verify binary integrity using SHA-256 checksums:

```text
c94e680a811d127c069ca3816aed2e55a582147de862c7ba5a8b2cbf72c724fd  UniversalClipboard-Setup-1.1.0.exe
0c4a0f2423688b935d3397202b738872f21d6ef497da356f31ef435dfceee41f  UniversalClipboard-Portable-1.1.0.exe
758e660d16f6e52d912f95e31fa05e579660fb76e6b8cdecfd5979bbf21e7d3c  UniversalClipboard-Android-1.1.0.apk
```

> **🛡️ Note on Windows SmartScreen ("Unknown Publisher")**: When launching the installer for the first time, Microsoft Defender SmartScreen may display: *"Windows protected your PC"*. Simply click **More info** &rarr; **Run anyway**. This is standard Windows behavior for newly released open-source software before community download reputation builds in Microsoft's telemetry cloud.

---

## ✨ Features in Version 1.1.0

- **👥 Unlimited Multi-Phone Pairing**:
  - Pair multiple compatible Android phones and tablets (Tecno, Samsung, Xiaomi/Redmi, Pixel, OnePlus, etc.) with one Windows workstation.
  - Distinct persistent device identifiers with custom renaming, individual disconnection, and unpairing without wiping other devices.
  - Windows clipboard broadcasts concurrently across all connected devices.
- **⚡ Seamless Bidirectional Clipboard Sharing**:
  - **PC ➔ Phone**: Copy on Windows (`Ctrl + C`) and immediately paste in any phone app.
  - **Phone ➔ PC (Zero-Tap)**: Optional Android Accessibility Service enables automatic copy sync without opening the app.
  - **1-Tap Quick Action**: Persistent notification button `[ 📋 Send to PC ]` and Quick Settings Tile for instant transfers.
- **🖥️ Smart Desktop Status & Devices Window**:
  - Real-time paired and active devices list with connection badges (`🟢 Active Now` vs `⚪ Paired (Offline)`).
  - Displays pairing QR code while waiting for connection, or tap "Pair Another Phone" to pair additional devices.
  - Dedicated "Download APK" tab with direct Wi-Fi download link and QR code.
- **🔄 Robust Reconnection Engine**:
  - Exponential backoff with jitter (2s–30s).
  - Monotonic connection epochs prevent stale socket callbacks from corrupting connection state.
  - Automatic UDP network discovery (`port 8766`) recovers seamlessly when router DHCP assigns a new IP address.
- **🔐 Hardware & OS-Backed Security**:
  - **AES-256-GCM Encryption**: All clipboard text and images encrypted with unique 96-bit IVs and 128-bit authentication tags.
  - **Windows DPAPI Storage**: Master keys protected by Windows DPAPI in `%APPDATA%\UniversalClipboard\config.json`.
  - **Android Keystore**: Master keys encrypted with hardware-backed Android Keystore.
  - **Replay Protection**: Mutual HMAC-SHA256 challenge-response handshake with 32-byte nonces.
  - **Echo-Loop Suppression**: Normalized line-ending SHA-256 hashing prevents infinite loop ping-pongs.

---

## 🚀 Quick Start Guide

### 1. Install on Windows

1. Download `UniversalClipboard-Setup-1.1.0.exe` and run the installer.
   - *If Windows Defender SmartScreen displays "Windows protected your PC":* Click **More info** &rarr; **Run anyway**.
2. The application will launch into your **Windows System Tray** (near the clock).
3. Right-click the tray icon and select **🖥️ Open Status Window** (or double-click the tray icon).

### 2. Install on Android

1. Download `UniversalClipboard-Android-1.1.0.apk` from your phone browser or via local Wi-Fi at `http://<PC_IP>:8765/download`.
2. Tap the APK to install (allow "Install unknown apps" if prompted).
3. Open the app and grant Camera and Notification permissions.
4. *If Android 13/14+ displays "Restricted setting" when enabling accessibility:* Tap **"Step 1: App Info (Allow)"**, tap the three dots (**⋮**) in the top-right corner of App Info, select **"Allow restricted settings"**, and confirm your phone PIN/fingerprint. Then tap **"Step 2: Accessibility"** and turn it ON.

### 3. Pair in Seconds

1. In the Windows status window, view the **Pair Device (QR Code)** tab.
2. On your phone, tap **Scan QR Code** and point your camera at the PC screen.
3. The Windows screen transitions immediately to **🟢 CONNECTED TO ANDROID**, showing your phone in the paired devices list.
4. To add another phone, tap **"➕ Pair Another Phone"** and scan from the second device. Both phones will sync concurrently!

---

## 🌐 Official Landing Website & Netlify Deployment

The project includes a self-contained, responsive production website in [`website/`](file:///website/):

- **Local Preview**: `python -m http.server 8080 --directory website` (open `http://localhost:8080`)
- **Netlify Deploy**: Publish directory `website` (see [`website/README.md`](file:///website/README.md) for full guide)
- **Central Configuration**: Managed in [`website/site-config.js`](file:///website/site-config.js)

---

## 📖 Detailed Documentation

- [Android Restricted Settings Guide](file:///docs/ANDROID_RESTRICTED_SETTINGS.md) — Resolution for Android 13/14+ sideloaded APK accessibility restrictions.
- [Multi-Device Pairing Guide](file:///docs/MULTI_DEVICE_GUIDE.md) — Unlimited multi-phone pairing, device manager, and concurrent synchronization.
- [Release Installation Guide](file:///docs/RELEASE_INSTALLATION_GUIDE.md) — Nontechnical step-by-step setup guide.
- [End-to-End Validation Guide](file:///docs/END_TO_END_TEST_GUIDE.md) — Test procedures, verification matrix, and unique test strings.
- [Known Limitations & Architecture Boundaries](file:///docs/KNOWN_LIMITATIONS.md) — Operating system restrictions and scope.
- [Release Verification Report](file:///docs/RELEASE_VERIFICATION_REPORT.md) — Exact file sizes, checksums, and signature verification.
- [Security Architecture & Threat Model](file:///docs/SECURITY.md) — Cryptographic protocol and security specifications.
- [Privacy Policy & Data Handling](file:///docs/PRIVACY.md) — Zero-telemetry, local LAN only, zero persistent clipboard history.

---

## 🧪 Developer Build & Test Instructions

### Running Python Tests

```bash
python -m pytest -v
# 21 passed
```

### Running Android Unit Tests

```bash
cd android
.\gradlew.bat testDebugUnitTest
# 7 passed
```

---

## 👥 Support & Attribution

- **Support Email**: `gmuraguri75@gmail.com`
- **Creator Attribution**: Built by [BAZIQHUE](https://baziqhue.co.ke/)
- **Parent Website**: [https://baziqhue.co.ke/](https://baziqhue.co.ke/)
- **License**: Universal Clipboard Sync is open-source software licensed under the **MIT License**.
