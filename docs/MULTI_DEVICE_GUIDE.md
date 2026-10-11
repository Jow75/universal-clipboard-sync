# Multi-Device Pairing & Management Guide

Universal Clipboard Sync supports **unlimited multi-phone pairing**, allowing one Windows workstation to maintain concurrent, authenticated synchronization with multiple Android phones, tablets, and testing devices simultaneously.

---

## 1. Architecture Overview

### Stable Device Identity
- Each paired Android device generates a cryptographically secure, persistent UUID on first launch stored in Android KeyStore-backed secure preferences (`getOrCreateClientId()`).
- The device transmits its stable ID alongside its hardware manufacturer and model (e.g. `Tecno Spark 10 Pro`, `Samsung Galaxy S24`, `Google Pixel 8`).
- Reconnecting after a Wi-Fi interruption, phone reboot, or screen lock reuses the existing device identity without creating duplicate pairing entries.

### Workstation Device Manager
- The Windows desktop application stores paired devices in persistent configuration (`%APPDATA%\UniversalClipboard\config.json`) protected by Windows DPAPI.
- The Status Window displays a real-time list of all paired devices with live status indicators (`🟢 Active Now` vs `⚪ Paired (Offline)`).
- Users can:
  - **Rename devices**: Assign custom human-readable labels (e.g. *"Work Phone"*, *"Personal Tecno"*, *"Bedside Tablet"*).
  - **Disconnect specific devices**: Drop the active socket for a specific phone without disconnecting other phones.
  - **Unpair devices**: Revoke pairing for one phone without affecting other pairings.

---

## 2. Pairing Multiple Phones

### Step-by-Step Pairing Workflow:
1. Open Universal Clipboard on your Windows computer. Double-click the System Tray icon to view the **Status Window**.
2. On the **🔗 Pair Phone** tab, view the live pairing QR code.
3. Open Universal Clipboard on **Phone 1** (e.g. Tecno Spark 10), tap **Scan QR Code**, and point the camera at the PC screen.
4. The Windows window transitions immediately to the **🟢 Connected** tab, showing Phone 1 active in the device list.
5. To pair **Phone 2** (e.g. Samsung Galaxy S24):
   - Tap **"➕ Pair Another Phone"** at the bottom of the Status Window (or switch to the "Pair Phone" tab).
   - The desktop displays a fresh ephemeral QR code.
   - On Phone 2, tap **Scan QR Code** and scan the screen.
   - Phone 2 pairs immediately! Both Phone 1 and Phone 2 are now actively connected and synchronizing!
6. Repeat for any additional Android phones or tablets.

---

## 3. Simultaneous Clipboard Synchronization & Loop Prevention

When multiple phones are connected:
1. **Windows ➔ All Phones**: Copying text or an image on Windows (`Ctrl + C`) broadcasts the encrypted payload to **all connected phones simultaneously**.
2. **Phone ➔ Windows**: Copying text on Phone 1 synchronizes immediately to the Windows clipboard.
3. **Loop Prevention**: Universal Clipboard normalizes line-endings and computes SHA-256 content hashes to suppress echo-loops. When Windows receives an update from Phone 1, it suppresses reflecting that content back to Phone 1.
