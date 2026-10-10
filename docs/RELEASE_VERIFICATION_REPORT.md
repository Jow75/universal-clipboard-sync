# Universal Clipboard Sync — Release Verification Report (v1.1.0)

**Report Date**: 2026-10-10  
**Target Platforms**: Windows 10, Windows 11 (x64) and Android (API 26–35)  
**Release Version**: `1.1.0` (Android versionCode: `2`, versionName: `"1.1.0"`)  
**Canonical Repository**: `Jow75/universal-clipboard-sync`  
**Git Branch**: `master`  

---

## 1. Verified Release Artifacts & Checksums

All build deliverables have been compiled, verified, and placed in `dist/`.

| Artifact File | Deliverable Type | File Size (Bytes) | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| **`UniversalClipboard-Setup-1.1.0.exe`** | Windows Setup Installer (Inno Setup 6) | 44,276,974 bytes | `a5df099ffbc718841f2172f21d250d0ba6c8e3c9336e08cc484d75e5f809c5ae` |
| **`UniversalClipboard-Portable-1.1.0.exe`** | Windows Standalone Portable Executable (PyInstaller) | 47,445,328 bytes | `be603914ae5341d291ac7ae2198e9840cd84b319346f86ecd00bdc7e7de547ce` |
| **`UniversalClipboard-Android-1.1.0.apk`** | Android Release APK (v2 Signed) | 5,698,075 bytes | `758e660d16f6e52d912f95e31fa05e579660fb76e6b8cdecfd5979bbf21e7d3c` |
| **`SHA256SUMS.txt`** | Checksum Verification Manifest | 276 bytes | `6f3801ea8f65e2365a1097fa668ef4ef3c6ce0fc5da4db2bf5fb731c3a649820` |
| **`download_qr.png`** | Verified Download QR Code Image | 19,418 bytes | `b2e45da812f865f1ee540b64be8721bf90eb912efc4d2843bb0dcab7d59b2d97` |

---

## 2. Android APK Package & Signature Verification

### 2.1 Package Metadata
- **Application ID**: `com.example.universalclipboard`
- **Version Code**: `2` (Incremented from `1` to enable in-place Android OS upgrades)
- **Version Name**: `"1.1.0"`
- **Minimum SDK**: `26` (Android 8.0 Oreo)
- **Target SDK**: `35` (Android 15 Vanilla Ice Cream)
- **Compile SDK**: `35`

### 2.2 APK Signature Verification (`apksigner`)
Command executed:
```powershell
apksigner verify --verbose --print-certs dist\UniversalClipboard-Android-1.1.0.apk
```
Output:
- **Verifies**: `true`
- **Verified using v1 scheme (JAR signing)**: `true`
- **Verified using v2 scheme (APK Signature Scheme v2)**: `true`
- **Verified using v3 scheme (APK Signature Scheme v3)**: `true`
- **Verified using v4 scheme**: `false`
- **Signer #1 Certificate DN**: `CN=Android Debug, O=Android, C=US`
- **Signer #1 Certificate SHA-256 Digest**: `0e4c6c06a38fe484ff7a884a22ad39ec1adfb6d3f237f3747d4e5659fb16922d`

### 2.3 Upgrade Safety & Compatibility
- **In-place Upgrade**: Users who installed previous debug/direct-download APKs signed with this consistent development certificate will be upgraded smoothly in-place by Android Package Manager without losing app data or Keystore pairing keys.
- **Signature Mismatch Protection**: If a user previously installed an APK signed with an unrelated private commercial keystore, Android will block the upgrade with `INSTALL_FAILED_UPDATE_INCOMPATIBLE`. In that case, the user must uninstall the old build before installing v1.1.0.

---

## 3. Automated Test Verification Results

### 3.1 Python Test Suite (Desktop)
- **Command**: `python -m pytest -v`
- **Total Tests**: 18
- **Passed**: 18
- **Failed**: 0
- **Duration**: 6.42s
- **Coverage Areas**: Connection lifecycle, duplicate socket superseding, Windows clipboard retry with backoff, DPAPI configuration persistence, AES-256-GCM cipher round-trip, hotkey dispatch, UDP physical LAN interface filtering, ephemeral pairing session TTL expiration, mutual HMAC-SHA256 challenge authentication, and UI window state transitions.

### 3.2 Android Unit Test Suite (JVM)
- **Command**: `.\android\gradlew.bat testDebugUnitTest`
- **Total Tests**: 7
- **Passed**: 7
- **Failed**: 0
- **Coverage Areas**: Text CRLF/LF normalization, cross-platform SHA-256 content hash consistency, HMAC-SHA256 authentication tag calculation, binary-to-hex conversion, and connection state machine enum integrity (`DISCONNECTED` -> `DISCOVERING` -> `CONNECTING` -> `AUTHENTICATING` -> `CONNECTED` -> `RECONNECTING` -> `ERROR`).

---

## 4. Download QR Code Verification

- **Artifact**: `dist/download_qr.png` / `docs/assets/download_qr.png`
- **Encoded Payload**: `https://github.com/Jow75/universal-clipboard-sync/releases/latest`
- **Verification Tool**: OpenCV 4.13.0 `QRCodeDetector().detectAndDecode()`
- **Result**: **PASS** — Exact match confirmed.

---

## 5. Download Links & Availability Status

| Platform / File | Canonical Link | Availability Status |
| :--- | :--- | :--- |
| **GitHub Releases Page** | `https://github.com/Jow75/universal-clipboard-sync/releases/latest` | Dependent on GitHub repo publication/tag push |
| **Windows Installer** | `https://github.com/Jow75/universal-clipboard-sync/releases/download/v1.1.0/UniversalClipboard-Setup-1.1.0.exe` | Staged locally in `dist/` |
| **Windows Portable** | `https://github.com/Jow75/universal-clipboard-sync/releases/download/v1.1.0/UniversalClipboard-Portable-1.1.0.exe` | Staged locally in `dist/` |
| **Android APK** | `https://github.com/Jow75/universal-clipboard-sync/releases/download/v1.1.0/UniversalClipboard-Android-1.1.0.apk` | Staged locally in `dist/` |
| **Local Wi-Fi Download** | `http://<YOUR_PC_IP>:8765/download` | **LIVE & ACTIVE** immediately whenever Windows app runs |
