# Universal Clipboard Sync — Comprehensive Implementation Plan

**Version:** 1.0.0  
**Status:** In Progress  
**Objective:** Transform Universal Clipboard Sync from an unhardened MVP into a stable, secure, zero-friction, QR-paired, reliable cross-device utility.

---

## Milestone 1: Baseline Establishment & Defect Confirmation
* [x] Complete inventory of all project files and dependencies.
* [x] Confirm root causes of reported bugs:
  * Ephemeral key generation on desktop.
  * Inconvenient token copying / manual transfer.
  * Android 10+ background clipboard reading sandbox.
  * Unauthenticated WebSocket endpoint.
  * Image URI permission denial on Android.
  * SHA-256 vs Java hashCode deduplication mismatch.
  * Multi-adapter virtual IP selection on Windows.
  * Java JDK 8 vs JDK 17 Gradle toolchain issue.
* [x] Create `docs/ENGINEERING_BASELINE.md`.
* [x] Create `docs/IMPLEMENTATION_PLAN.md`.

---

## Milestone 2: Foundation (Credential Persistence, Security & Network Discovery)
* [ ] **Windows Credential & Configuration Persistence:**
  * Implement `desktop/config.py` to persist device identity, long-term pairing credentials, and settings under `%APPDATA%\UniversalClipboard\config.json`.
  * Support secure DPAPI / encrypted storage or secure file permissions.
  * Ensure Windows restart reuses the existing pairing secret.
* [ ] **Android Secure Storage:**
  * Implement Android Keystore or EncryptedSharedPreferences for storing device identity and paired computer secrets.
  * Ensure Android restart reuses credentials.
* [ ] **Network Interface Filtering:**
  * Upgrade `desktop/main.py`'s `get_ip()`:
    * Enumerate physical network interfaces.
    * Prioritize Wi-Fi (`wlan`) and physical Ethernet (`eth`) interfaces.
    * Explicitly ignore virtual adapters (WSL, Hyper-V, VirtualBox, VMware, Docker, TAP/TUN).
* [ ] **Authenticated Protocol & Session Establishment:**
  * Implement handshake protocol over WebSocket before exchanging clipboard data.
  * Verify shared secret / session challenge.
  * Reject unauthenticated clients.
* [ ] **Automated Reconnection:**
  * Android client reconnection with exponential backoff and randomized jitter.
  * Clear UI state tracking: `Disconnected`, `Connecting`, `Connected`, `Pairing Required`.

---

## Milestone 3: Reliable Synchronization & Android Restrictions Handling
* [ ] **Unified Cross-Platform Message Protocol:**
  * Standardize JSON message envelope across Python and Kotlin:
    ```json
    {
      "v": 2,
      "id": "uuid4",
      "type": "text|image",
      "data": "...",
      "ts": 1771900000,
      "hash": "sha256-hex"
    }
    ```
  * Enforce maximum message limits (e.g. 50MB for raw frames, 10MB compressed images).
  * Replay protection via timestamp freshness check.
* [ ] **Cross-Platform Deduplication & Echo-Loop Prevention:**
  * Both Windows and Android compute standard SHA-256 digests over normalized payload bytes.
  * Normalize line endings (`\r\n` to `\n`) before computing hashes.
* [ ] **Android 10+ Background Clipboard Restrictions Solution:**
  * Maintain prominent persistent notification with an explicit action button: `[ Sync Clipboard Now ]`.
  * Implement a Quick Settings Tile (`ClipboardSyncTileService`) allowing 1-tap clipboard push from any app without opening the full UI.
  * Automatic synchronization remains active when `MainActivity` is in the foreground.
  * Transparently document Android platform limitations in the UI.
* [ ] **Android Image URI Permissions & Sharing Fix:**
  * Setup `FileProvider` (`com.example.universalclipboard.fileprovider`) for stored clipboard images.
  * Grant `FLAG_GRANT_READ_URI_PERMISSION` on the `ClipData` URI so WhatsApp, Slack, Browser, and other apps can paste the image seamlessly.

---

## Milestone 4: Frictionless QR Pairing Experience
* [ ] **Ephemeral QR Pairing Protocol:**
  * Desktop creates a short-lived pairing session (expires in 120 seconds).
  * Generates random session ID, ephemeral token, host IP, and port.
  * Formats QR payload as a compact JSON / URI string:
    `uniclip://pair?s=<session_id>&t=<token>&h=<host>&p=8765&exp=<timestamp>`
* [ ] **Desktop QR Code Display:**
  * Implement desktop pairing window (using Tkinter or Pillow + system viewer / tray dialog) rendering a clean, scannable QR code.
  * Include a countdown timer and "Cancel" button.
* [ ] **Android QR Scanner:**
  * Integrate ML Kit Barcode Scanning / ZXing embedded scanner.
  * Clean camera permission flow: request camera only when user taps "Scan QR Code".
  * Parse QR payload, validate expiration, perform handshake, save paired credentials.
  * Show immediate feedback and switch to Connected state.

---

## Milestone 5: Network Flexibility & Cross-Network Strategy
* [ ] **Local Network Discovery:**
  * Implement UDP broadcast beacon / mDNS so Android can discover Windows IP changes automatically without re-pairing.
* [ ] **Cross-Network Architecture:**
  * Produce `docs/NETWORK_ARCHITECTURE.md` documenting relay designs (WebRTC TURN / encrypted WebSocket relay) for non-LAN setups.

---

## Milestone 6: Verification & Automated Testing
* [ ] Python test suite: crypto, protocol, pairing, deduplication, interface filtering.
* [ ] Android test suite: Kotlin unit tests, protocol validation, Keystore tests.
* [ ] Build verification:
  * Android debug and release APK builds (`gradlew assembleDebug`, `gradlew assembleRelease`).
  * PyInstaller Windows `.exe` build with correct asset paths.
* [ ] Create `docs/TEST_REPORT.md`.

---

## Milestone 7: Release Readiness & Distribution Preparation
* [ ] Complete `README.md` with installation guides for Windows and Android.
* [ ] Create `docs/SECURITY.md` detailing the threat model and cryptographic guarantees.
* [ ] Prepare GitHub Actions workflow (`.github/workflows/ci.yml`) for multi-platform builds.
* [ ] Package build artifacts: Windows `.exe` and Android `.apk`.
