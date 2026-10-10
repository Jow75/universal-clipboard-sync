# Universal Clipboard Sync — Physical Smoke Test Results Template

Fill out this template after running the tests in `docs/PHYSICAL_DEVICE_SMOKE_TEST.md`.  
Mark each test item as `[PASS]`, `[FAIL]`, `[NOT SURE]`, or `[NOT TESTED]`.

---

## 1. Test Environment Details

- **Date of Test**: 
- **Windows Version**: Windows 10 / Windows 11
- **Windows Executable Path**: `C:\Users\gmura\Music\Copy and Paste\dist\UniversalClipboard.exe`
- **Phone Model**: (e.g., Samsung Galaxy S23, Google Pixel 8, Xiaomi 13)
- **Phone Android Version**: (e.g., Android 13, Android 14, Android 15)
- **Connected to Same Wi-Fi Router?**: Yes / No

---

## 2. Pre-Flight Safety Checks (Steps 1 – 5)

- [ ] **Step 1: Checksums Verified**: Executable and APK SHA-256 hashes matched expected build values.
- [ ] **Step 2: Configuration Backed Up**: Ran backup PowerShell script; backup verified on Desktop (or confirmed folder not yet present).
- [ ] **Step 3: Old App Closed**: Verified port 8765 is clear and old clipboard app/script is not running.
- [ ] **Step 4 & 5: Android Installation Outcome**:
  - [ ] Installed as In-Place Update (No signature conflict).
  - [ ] Signature conflict detected: Installation cancelled without uninstalling (old app kept intact).
  - [ ] App permissions granted (Camera + Notifications).

---

## 3. Physical Smoke Test Checklist (Steps 6 – 10)

### A. Initial Launch & QR Pairing (Steps 6 & 7)
- [ ] **PC Launch**: `UniversalClipboard.exe` started cleanly with icon in System Tray.
- [ ] **Pairing Window**: Clicked "Pair Phone (QR Code)"; QR code appeared with live 3-minute timer.
- [ ] **Android Scanner**: Tapped "Scan QR Code to Pair" in Android app; camera viewfinder opened.
- [ ] **Pairing Handshake**: Scanned QR code on PC monitor; phone beeped and showed green "Connected" card.
- [ ] **PC Notification**: Windows notification popped up confirming phone connected.

### B. Text Synchronization (Step 8)
- [ ] **PC ➔ Phone Text**: Copied text on PC (`Ctrl + C`); pasted matching text on phone.
- [ ] **Phone ➔ PC (Notification)**: Copied text on phone, tapped `[ 📋 Send to PC ]` in notification drawer, pasted into PC Notepad (`Ctrl + V`).
- [ ] **Phone ➔ PC (Quick Settings)**: Copied text on phone, tapped "Sync to PC" tile in Quick Settings, pasted into PC Notepad.
- [ ] **Unicode & Multiline**: Tested copying text with emojis (`🚀✨`) and multiple paragraphs; formatted text transferred intact.
- [ ] **Echo Loop Check**: Transferred text did NOT endlessly bounce back and forth between PC and phone.

### C. Reconnection & Restart Resilience (Step 9)
- [ ] **PC App Restart**: Quit `UniversalClipboard.exe` from system tray, reopened it. Phone automatically reconnected within 15 seconds without scanning any QR code.
- [ ] **Phone App Restart**: Closed or force-stopped Android app, reopened it. App automatically reconnected to PC without scanning any QR code.
- [ ] **Wi-Fi Drop Recovery**: Turned off phone Wi-Fi, turned it back on. Phone automatically reconnected once back on home Wi-Fi.

### D. Image Synchronization (Step 10)
- [ ] **PC ➔ Phone Screenshot**: Took screenshot on PC (`Win + Shift + S`); phone received notification "Image copied from PC".
- [ ] **Cross-App Image Paste**: Pasted received image on phone into an app (e.g., WhatsApp / Slack / Gmail / Notes).
  - *Name of App Tested*: ________________
  - *Did the image paste successfully?*: Yes / No
- [ ] **Phone ➔ PC Image**: Copied image in phone Gallery, tapped `[ 📋 Send to PC ]`; pasted into PC Paint / photo editor.

---

## 4. Issues & Diagnostic Log

- **Any error messages seen on screen?**:
  *(If any, type them here)*

- **Diagnostic Log Contents**:
  *(Right-click the PC tray icon -> click "View Diagnostic Logs". If any errors or unusual lines are present, paste the last 20 lines here)*

---

## 5. Overall Assessment
- [ ] **PASSED** — Text and image synchronization work reliably; restarts recover cleanly.
- [ ] **PARTIALLY WORKING** — Some features work, but specific issues occurred (detailed above).
- [ ] **BLOCKED** — Could not pair or connect.
