# Universal Clipboard Sync — Known Limitations & System Scope

This document provides transparent, honest documentation of the operational boundaries, Android operating system constraints, and security considerations in **Universal Clipboard Sync v1.1.0**.

---

## 1. Android Background Clipboard Restrictions (Android 10+)

### Operating System Constraint
Starting with Android 10 (API 29), Google introduced strict privacy restrictions preventing apps from reading the system clipboard while running in the background. Even an active foreground service cannot silently read `ClipboardManager.getPrimaryClip()` unless the app is currently in the active foreground with user focus.

### Universal Clipboard Solution & Limitations
To comply with Android security and preserve battery life without deceptive hacks, Universal Clipboard Sync provides three tiered approaches:
1. **Accessibility Service (Recommended)**: By enabling the optional Accessibility Service in Android Settings, the app receives user text selection and copy events across applications.
   - *Limitation*: Requires the user to explicitly toggle the Accessibility permission once in Android Settings. Some highly restricted enterprise/work-profile environments may disallow third-party accessibility services.
2. **Foreground Notification Action (`📋 Send to PC`)**: If Accessibility is not enabled, the user can copy text anywhere, pull down the notification bar, and tap `Send to PC`.
   - *Limitation*: Requires 1 user tap (substantially better than opening the full app, but not zero-tap).
3. **Quick Settings Tile**: A quick settings toggle allows sending the clipboard from any screen.
   - *Limitation*: Requires the user to add the tile to their Android Quick Settings panel.

---

## 2. Network Topology & Scope

### Local Network Only (No Cloud Relay)
- **Direct LAN Connection**: Universal Clipboard Sync operates strictly over the local area network (LAN / Wi-Fi) using peer-to-peer WebSockets and UDP discovery.
- **No Cloud Servers**: Clipboard data **never** leaves your local Wi-Fi network and is never routed through third-party cloud servers or relays.
- **Limitation**: Clipboard synchronization will **not** work if your Windows PC and Android phone are on different networks (for example, if the phone is on mobile data (4G/5G) and the PC is on home Wi-Fi, or if public/guest Wi-Fi has client isolation enabled).
- **Subnet / Multi-Adapter**: If your PC has multiple network adapters (e.g. active VPN or VirtualBox adapters), the app selects the physical LAN adapter. If an aggressive corporate VPN tunnels all local traffic, local socket binding may be restricted.

---

## 3. Windows SmartScreen & Code Signing

### Microsoft Defender SmartScreen
- **Limitation**: Windows 10/11 may display a *"Windows protected your PC"* SmartScreen warning when running `UniversalClipboard-Setup-1.1.0.exe` or `UniversalClipboard-Portable-1.1.0.exe`.
- **Reason**: The executable is built as an open-source project and is not signed with an enterprise commercial Authenticode certificate (which requires an annual certificate authority subscription).
- **Resolution**: Click **More info** -> **Run anyway**. The binary is completely open-source, reproducible, and verifiable via the published SHA-256 checksums in `SHA256SUMS.txt`.

---

## 4. Android APK Installation & Signature Upgrade

### Sideloading ("Install Unknown Apps")
- **Limitation**: Downloading the APK directly outside Google Play requires Android users to approve "Install unknown apps" for their browser or file manager.
- **Upgrade Compatibility**: The v1.1.0 APK is signed with a consistent signature scheme (v2 signature scheme). If upgrading from an existing installation, the application ID `com.example.universalclipboard` and signing certificate must match. If you previously installed a version built with a different developer key, Android will refuse an in-place upgrade until the mismatched version is uninstalled.

---

## 5. Image & Large File Payloads

- **Text Synchronization**: Normal text, URLs, markdown, and unicode text sync instantaneously.
- **Image Synchronization**: Desktop and Android support PNG/JPEG image exchange. However, extremely large payloads (>10 MB) may experience minor latency or buffer limits over congested 2.4 GHz Wi-Fi channels.

---

## 6. Physical Device Testing Boundaries

- **Simulated & Automated Verification**: 100% of cryptographic routines, DPAPI storage, WebSocket handshakes, state machine transitions, backoff algorithms, and UI transitions are verified by automated test suites (18 Python tests, 7 Android unit tests).
- **Physical Device Gate**: Physical touch interactions on specific Android OEM flavors (Samsung OneUI, Xiaomi MIUI/HyperOS, Google Pixel) may exhibit vendor-specific battery optimization behavior. Users should exempt the Universal Clipboard app from aggressive OEM battery killers (e.g. "Don't optimize battery").
