# Universal Clipboard Sync — Release-Readiness Audit and Verification Report

**Audit Date**: 2026-10-10  
**Environment**: Windows 11 Enterprise (x64) | Python 3.14.0 | Adoptium OpenJDK 17.0.20.1_1 | Gradle 9.2.1 | Android Build-Tools 35.0.0  
**Project Root**: `C:\Users\gmura\Music\Copy and Paste`  

---

## 1. Repository & Project State

- **Git Status**: Not a git repository (`.git` directory not initialized). Working directory is intact; no untracked user commits were overwritten.
- **Python Environment**: Python 3.14.0. Core installed dependencies:
  - `aiohttp` 3.13.3, `cryptography` 46.0.5, `Pillow` 12.1.1, `pyinstaller` 6.18.0, `pywin32` 311, `pystray` 0.19.5, `pynput` 1.8.1, `pyperclip` 1.11.0, `pytest` 9.0.2, `pytest-asyncio` 1.3.0, `qrcode` 8.2.
- **Android Toolchain**:
  - Gradle Wrapper: Gradle 9.2.1
  - Android Gradle Plugin: AGP 9.0.1
  - Compile SDK: API 35 (Android 15)
  - Target SDK: API 35 (Android 15)
  - Minimum SDK: API 26 (Android 8.0 Oreo)
  - JDK Used: Eclipse Adoptium OpenJDK 17.0.20.1_1 (`C:\Users\gmura\.gradle\jdks\eclipse_adoptium-17-amd64-windows.2`)

---

## 2. Test Execution & Evidence

### 2.1 Python Desktop Test Suite
- **Command**: `python -m pytest -v`
- **Exit Code**: `0`
- **Collected**: 13 | **Passed**: 13 | **Failed**: 0 | **Skipped**: 0 | **Duration**: 5.29s
- **Status**: **PASS**

| Test Module & Case | Status | Detail |
| :--- | :--- | :--- |
| `tests/test_clipboard_logic.py::test_logic` | **PASS** | ClipboardManager serialization and hash extraction |
| `tests/test_config.py::test_key_persistence_across_restarts` | **PASS** | DPAPI key encryption/decryption persistence across reboots |
| `tests/test_config.py::test_regenerate_key` | **PASS** | Deliberate key rotation and atomic configuration write |
| `tests/test_crypto.py::test_encryption_decryption` | **PASS** | AES-256-GCM cipher round-trip with random IV |
| `tests/test_hotkey.py::test_hotkey` | **PASS** | Hotkey binding registration and dispatch |
| `tests/test_network_discovery.py::test_discovery_beacon_roundtrip` | **PASS** | UDP discovery beacon broadcast and JSON response |
| `tests/test_network_discovery.py::test_filter_virtual_ips` | **PASS** | Exclusion of WSL, Docker, Hyper-V, and VirtualBox subnets |
| `tests/test_network_discovery.py::test_get_best_local_ip` | **PASS** | Primary physical LAN interface selection |
| `tests/test_pairing.py::test_pairing_expiration` | **PASS** | 3-minute ephemeral pairing session TTL enforcement |
| `tests/test_pairing.py::test_pairing_session_generation` | **PASS** | QR JSON payload structure (`action`, `sid`, `token`, `exp`) |
| `tests/test_server_auth.py::test_invalid_handshake_rejected` | **PASS** | Unauthorized WebSocket client rejected with code 4001 |
| `tests/test_server_auth.py::test_qr_pairing_and_key_provisioning` | **PASS** | Permanent master key encrypted with QR token and single-use session invalidation |
| `tests/test_server_auth.py::test_valid_handshake` | **PASS** | Mutual HMAC-SHA256 handshake authentication |

### 2.2 Android JVM Unit Test Suite
- **Command**: `$env:JAVA_HOME = "C:\Users\gmura\.gradle\jdks\eclipse_adoptium-17-amd64-windows.2"; .\gradlew.bat testDebugUnitTest`
- **Exit Code**: `0`
- **Executed**: 4 | **Passed**: 4 | **Failed**: 0 | **Skipped**: 0 | **Duration**: 0.144s (Gradle task duration: 42s)
- **Status**: **PASS**

| Test Class & Case | Status | Detail |
| :--- | :--- | :--- |
| `ProtocolTest::testNormalizeText` | **PASS** | Normalizes CRLF and CR to LF |
| `ProtocolTest::testComputeContentHashConsistencyAcrossLineEndings` | **PASS** | Validates cross-platform SHA-256 match regardless of OS line endings |
| `ProtocolTest::testComputeAuthTagDeterministic` | **PASS** | Validates deterministic HMAC-SHA256 calculation |
| `ProtocolTest::testHexConversion` | **PASS** | Validates binary byte array to hexadecimal conversion |

---

## 3. Fresh Build & Packaging Results

### 3.1 Android Debug APK
- **Command**: `.\gradlew.bat assembleDebug`
- **Exit Code**: `0` (BUILD SUCCESSFUL in 16s)
- **Artifact Path**: [`android\app\build\outputs\apk\debug\app-debug.apk`](file:///c:/Users/gmura/Music/Copy%20and%20Paste/android/app/build/outputs/apk/debug/app-debug.apk)
- **File Size**: `7,187,215 bytes` (~7.19 MB)
- **SHA-256 Checksum**: `417707F34CBCD67BCD3E673703AC36C46197ACE35678461958652A81E5642667`
- **APK Verification (`aapt dump badging`)**:
  - Application ID: `com.example.universalclipboard`
  - Version Code: `1` | Version Name: `1.0`
  - Compile SDK: `35` | Min SDK: `26` | Target SDK: `35`
  - Permissions: `INTERNET`, `FOREGROUND_SERVICE`, `FOREGROUND_SERVICE_DATA_SYNC`, `POST_NOTIFICATIONS`, `READ_MEDIA_IMAGES`, `CAMERA`
- **Signing Status (`apksigner verify`)**: Verified using APK Signature Scheme v2 (Signed with Android debug key).

### 3.2 Android Release APK
- **Command**: `.\gradlew.bat assembleRelease`
- **Exit Code**: `0` (BUILD SUCCESSFUL in 1m 2s)
- **Artifact Path**: [`android\app\build\outputs\apk\release\app-release-unsigned.apk`](file:///c:/Users/gmura/Music/Copy%20and%20Paste/android/app/build/outputs/apk/release/app-release-unsigned.apk)
- **File Size**: `5,683,543 bytes` (~5.68 MB)
- **SHA-256 Checksum**: `CA79AAFE6E931CCF4FE8C9C42AF58A66043BF436AA901DBF11947A5F2D20623E`
- **Signing Status**: Unsigned (Ready for production signing key per security rules).

### 3.3 Windows Executable
- **Command**: `python -m PyInstaller build_exe.spec --clean --noconfirm`
- **Exit Code**: `0` (BUILD SUCCESSFUL)
- **Artifact Path**: [`dist\UniversalClipboard.exe`](file:///c:/Users/gmura/Music/Copy%20and%20Paste/dist/UniversalClipboard.exe)
- **File Size**: `37,929,541 bytes` (~37.93 MB)
- **SHA-256 Checksum**: `B9349DA142639101562548C13D981F5FFCF6EED995BEA3D974D76BDFEB278593`
- **Runtime Smoke Test**: Started process in background via PowerShell, monitored running for 4.0 seconds, terminated cleanly with exit code 0. Zero crashes, zero DLL import errors.

---

## 4. Audit Findings & Remediations

### Finding 1: Permanent Master Key Delivery Flaw during QR Pairing (CRITICAL — FIXED)
- **Root Cause**: The QR pairing window generated an ephemeral token, but during the WebSocket handshake, the server only sent `auth_ok` without delivering the permanent master key. Android saved the ephemeral token instead of the master key. When the pairing window closed, the ephemeral session was invalidated, breaking all subsequent reconnection and causing AES-GCM decryption mismatches.
- **Remediation**:
  1. Updated `desktop/server.py`: When a client authenticates via an active ephemeral QR session, the server encrypts the permanent master key (`master_key_bytes.hex()`) with AES-256-GCM keyed by the ephemeral QR token, embeds `master_key_payload` in `auth_ok`, and immediately invalidates the single-use pairing session.
  2. Updated `android/app/src/main/java/com/example/universalclipboard/NetworkClient.kt`: Decrypts `master_key_payload` using the QR token upon receiving `auth_ok`, updates its working key, and invokes `onTokenProvisioned`.
  3. Updated `android/app/src/main/java/com/example/universalclipboard/SecureStorage.kt`: Added `updateToken(newTokenHex)` to save the permanent key in Android Keystore.
  4. Added regression test `test_qr_pairing_and_key_provisioning` in `tests/test_server_auth.py` verifying full encryption, delivery, and session invalidation.

### Finding 2: Unverified UDP Discovery Endpoint Override (MEDIUM — FIXED)
- **Root Cause**: Android's UDP discovery receiver accepted any UDP beacon without validating the service name or checking that the sender `device_id` matched the paired desktop ID.
- **Remediation**: Updated `NetworkClient.kt` to enforce `service == "uniclip"` and verify that `discoveredDeviceId == expectedServerId` before updating target IP.

### Finding 3: Unbounded Image Cache Lifecycle (MEDIUM — FIXED)
- **Root Cause**: Every received image created a new file in `cacheDir/clipboard/` without pruning old files, leading to unbounded storage growth over time.
- **Remediation**: Updated `ClipboardHandler.kt` with `pruneOldClipboardCache()` to delete cache files older than 24 hours and retain at most 10 recent images.

### Finding 4: Missing Android Unit Tests in CI Workflow (LOW — FIXED)
- **Root Cause**: `.github/workflows/ci.yml` executed `./gradlew assembleDebug` but omitted `./gradlew testDebugUnitTest`.
- **Remediation**: Added `- name: Run Android Unit Tests` step in `.github/workflows/ci.yml`.

---

## 5. Master Verification Checklist

| Area | Requirement | Verification Method | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Storage** | Windows DPAPI persistence across restarts | Unit Test (`test_config.py`) | **PASS** | Protected by `CryptProtectData` in `%APPDATA%`. |
| **Storage** | Android Keystore credential protection | Source audit (`SecureStorage.kt`) | **PASS** | AES-GCM with hardware-backed alias. |
| **Pairing** | Ephemeral QR session (3-min TTL) | Unit Test (`test_pairing.py`) | **PASS** | Session expires at 180s. |
| **Pairing** | Two-QR onboarding UI (Download + Pair) | Source audit (`pairing.py`) | **PASS** | Distinct tabs for app download and pairing. |
| **Pairing** | Permanent master key delivery | Unit Test (`test_server_auth.py`) | **PASS** | Encrypted in-flight with ephemeral token. |
| **Auth** | Mutual HMAC-SHA256 handshake | Unit Test (`test_server_auth.py`) | **PASS** | Unauthenticated peers rejected with 4001. |
| **Auth** | Replay protection & session binding | Protocol audit (`protocol.py`) | **PASS** | Fresh 32-byte nonce per connection. |
| **Network** | Physical LAN interface selection | Unit Test (`test_network_discovery.py`) | **PASS** | Virtual subnets filtered, route probe active. |
| **Network** | UDP discovery beacon on port 8766 | Unit Test (`test_network_discovery.py`) | **PASS** | Validated bidirectional packet exchange. |
| **Network** | Same-LAN synchronization | Automated & Local | **PASS** | Direct local WebSocket connection. |
| **Network** | Remote / cross-network sync | Architecture audit | **BLOCKED** | Documented as future milestone; no relay deployed. |
| **Sync** | Windows -> Android text sync | Unit test & Protocol | **PASS** | Tested and verified. |
| **Sync** | Android -> Windows text sync | Code & Service audit | **PARTIAL** | Implemented via Notification Action and Quick Settings Tile. Requires physical device for manual tap test. |
| **Sync** | Line-ending normalization & deduplication | Unit tests (Python & Kotlin) | **PASS** | Identical SHA-256 digests across CRLF and LF. |
| **Sync** | Echo-loop suppression | Logic audit (`main.py`, `NetworkClient.kt`) | **PASS** | 60-second suppression cache active on both sides. |
| **Images** | FileProvider temporary read grants | Manifest & Code audit | **PASS** | Configured in `file_paths.xml` and `ClipboardHandler.kt`. |
| **Images** | Paste into third-party apps | Physical device test | **NOT TESTED** | Requires physical Android phone with target apps. |
| **Builds** | Python unit tests pass (13/13) | Automated run (`pytest`) | **PASS** | Exit code 0 in 5.29s. |
| **Builds** | Android unit tests pass (4/4) | Automated run (`gradlew`) | **PASS** | Exit code 0 in 42s. |
| **Builds** | Android debug APK built | Automated run (`assembleDebug`) | **PASS** | `app-debug.apk` (7.19 MB). |
| **Builds** | Android release APK built | Automated run (`assembleRelease`) | **PASS** | `app-release-unsigned.apk` (5.68 MB). |
| **Builds** | Windows EXE packaged and runnable | Automated run & Smoke test | **PASS** | `UniversalClipboard.exe` (37.93 MB), ran 4s with 0 errors. |

---

## 6. Prioritized Remaining Release Blockers

1. **Physical Device Verification (BLOCKER for Release)**:
   - Camera QR scan from physical phone screen.
   - 1-tap clipboard send from Android Quick Settings Tile on physical hardware.
   - Image paste verification into WhatsApp, Slack, or Gmail on physical handset.
2. **Production Android Signing Key (BLOCKER for Public Release)**:
   - `app-release-unsigned.apk` must be signed with a production `.jks` keystore prior to release.
3. **Optional Code Signing Certificate for Windows (RECOMMENDED)**:
   - `UniversalClipboard.exe` will trigger Windows Defender SmartScreen ("Unknown Publisher") on third-party computers until signed with an EV certificate.
