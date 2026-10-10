# Beginner-Friendly Physical Device Smoke Testing Guide

This guide walks you step-by-step through testing the new Universal Clipboard Sync build on your Windows computer and Android phone.

Follow these **11 steps in exact order**. Every step is designed to be safe, transparent, and completely reversible.

---

## Overview of Verification Status

| Feature / Component | Automated Verification Status | Physical Device Status |
| :--- | :--- | :--- |
| **Windows Executable Build** | ✅ Verified: SHA-256 matches build hash | Ready for local launch |
| **Android Debug APK Build** | ✅ Verified: SHA-256 & v2 signature match | Ready for phone transfer |
| **HMAC-SHA256 Handshake Protocol** | ✅ Verified in 13 Python tests | Pending physical test |
| **AES-256-GCM Encryption / Decryption** | ✅ Verified in automated unit tests | Pending physical test |
| **QR Code Generation & 3-Min Expiry** | ✅ Verified in automated unit tests | Pending camera scan test |
| **Text Sync (PC ➔ Phone & Phone ➔ PC)** | ✅ Verified in network simulation | **Requires physical phone test** |
| **Notification Action & Quick Tile** | ✅ Verified in Android unit tests | **Requires physical phone test** |
| **Image Sync & Cross-App Pasting** | ⚠️ Protocol verified; OS clipboard varies | **Requires physical app test** |
| **Reconnection after App Restart / Wi-Fi Drop** | ✅ Verified in loopback simulation | **Requires physical network test** |

---

## Step 1: Verify the Files and Checksums

Before testing, verify that the files on your computer match the verified builds.

### Run in PowerShell:
```powershell
Get-FileHash -Path "C:\Users\gmura\Music\Copy and Paste\dist\UniversalClipboard.exe", "C:\Users\gmura\Music\Copy and Paste\android\app\build\outputs\apk\debug\app-debug.apk" -Algorithm SHA256 | Select-Object Path, Hash | Format-List
```

### What You Should See:
* **For `UniversalClipboard.exe`**:
  `7DA31B0607968C2D544823EC8DB81BEDB456FF121683E95E0D5D26D63867996E`
* **For `app-debug.apk`**:
  `417707F34CBCD67BCD3E673703AC36C46197ACE35678461958652A81E5642667`

*If both hashes match, your build artifacts are intact and safe to proceed.*

---

## Step 2: Back Up Your Configuration and Confirm

Ensure your configuration is backed up to a timestamped folder on your Desktop.

### Run in PowerShell:
```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$appDataDir = "$env:APPDATA\UniversalClipboard"
$backupDir = "$env:USERPROFILE\Desktop\UniversalClipboard_Backup_$timestamp"

if (Test-Path $appDataDir) {
    Copy-Item -Path $appDataDir -Destination $backupDir -Recurse
    Write-Host "✅ Configuration backed up to: $backupDir" -ForegroundColor Green
    Get-ChildItem -Path $backupDir | Select-Object Name, Length | Format-Table -AutoSize
} else {
    Write-Host "ℹ️ No %APPDATA%\UniversalClipboard folder exists yet." -ForegroundColor Yellow
    Write-Host "This is normal: your previous version ran in-memory only. No backup required!" -ForegroundColor Green
}
```

---

## Step 3: Close the Old Desktop Application Safely

Both versions use network port **8765**. You must close the old version before running the new build.

1. **Check the System Tray**: Look near your Windows clock (click the `^` arrow if hidden). If you see an older clipboard icon, right-click it and choose **Quit** or **Exit**.
2. **If you ran the old app via Python script**:
   - If a terminal window is running `python desktop/main.py`, click inside the terminal and press `Ctrl + C`.
   - To safely check for any running Universal Clipboard Python process without terminating other Python programs:
     ```powershell
     Get-CimInstance Win32_Process -Filter "Name = 'python.exe' or Name = 'pythonw.exe'" | Where-Object { $_.CommandLine -like "*UniversalClipboard*" -or $_.CommandLine -like "*desktop/main.py*" -or $_.CommandLine -like "*desktop\main.py*" } | Select-Object ProcessId, CommandLine
     ```
     *(If a process appears, note its `ProcessId` and run `Stop-Process -Id <ProcessId>`).*
3. **If you previously ran an executable**:
   ```powershell
   Get-Process UniversalClipboard -ErrorAction SilentlyContinue
   ```
   *(If listed, run `Stop-Process -Name UniversalClipboard`).*

---

## Step 4: Decide Whether Android Can Be Updated Safely

Understand the Android installation situation before touching your phone:

1. Both the old and new apps use the exact same package ID: `com.example.universalclipboard`.
2. **Can Android update in-place?**:
   - If your phone's app was built from this PC's debug keystore, Android will update it in-place and keep all permissions.
   - If your phone's app was built with a different key, Android will refuse the update with **"App not installed as package conflicts with an existing package"**.
3. **What is preserved or lost?**:
   - An in-place update preserves all data.
   - If you must uninstall the old app to resolve a signature conflict, Android deletes the old app's local settings (its old server IP and old manual token). Because the old app did not use encrypted cloud data, no irreplaceable data is lost.
   - **Recommendation**: If you wish to remember the old app's settings, open the old app and write down the IP and token on paper before testing.

---

## Step 5: Install the Android Test Build

1. Locate the debug APK on your computer:
   `C:\Users\gmura\Music\Copy and Paste\android\app\build\outputs\apk\debug\app-debug.apk`
2. Transfer `app-debug.apk` to your phone:
   - Connect via USB cable and place it into your phone's **Downloads** folder, **OR**
   - Share it to yourself via Google Drive or local file transfer.
3. On your phone, open your **Files** or **Downloads** app and tap **`app-debug.apk`**.
   - **If Android shows "App not installed: Signature conflict" (or package conflict)**:
     **STOP AND CANCEL.** Tap **Done** or **Cancel**. Do **NOT** uninstall your existing app. A signature conflict means the app on your phone was signed with a different key than this computer's debug keystore. Leave the existing app in place and report this result.
5. Open the app and grant permissions:
   - **Camera**: Tap *"While using the app"* (required for scanning the PC screen).
   - **Notifications**: Tap *"Allow"* (required for background service & the 1-tap Send button).

---

## Step 6: Start the New Windows Executable

1. Navigate to: `C:\Users\gmura\Music\Copy and Paste\dist\`
2. Double-click **`UniversalClipboard.exe`**.
3. **If Windows SmartScreen appears**:
   - Click **"More info"**.
   - Click **"Run anyway"**.
4. **If Windows Defender Firewall prompts for network access**:
   - Check the box for **"Private networks, such as my home or work network"**.
   - **Uncheck** "Public networks".
   - Click **"Allow access"**.
   *(Note: The server only listens on your local Wi-Fi router. Never allow public networks).*
5. **Verify the server is running**:
   - Look in the System Tray (near the clock). You will see the **Universal Clipboard lightning icon**.
   - Right-click the icon to verify the menu shows:
     - `Status: Waiting for phone`
     - `IP: 192.168.x.x`
     - `Port: 8765`
     - `📱 Pair Phone (QR Code)`
     - `📄 View Diagnostic Logs`

---

## Step 7: Pair Using the QR Code

1. **On your Windows PC**:
   - Right-click the tray icon and click **`📱 Pair Phone (QR Code)`**.
   - A window appears titled **"Universal Clipboard — Connect & Pair"** with a live QR code and a 3-minute countdown timer.
2. **On your Android Phone**:
   - Open the Universal Clipboard app.
   - Tap **`📷 Scan QR Code to Pair`**.
   - Point your phone camera at the QR code on your PC monitor.
3. **What success looks like**:
   - Phone vibrates and displays: *"✅ Paired with Windows PC successfully!"*.
   - Phone screen changes to a green **Connected** status card showing your PC name and IP.
   - On Windows, a notification pops up: *"Phone connected: [Phone Model]"*.
   - The PC pairing window automatically closes.
4. **What failure looks like**:
   - If timer reaches 00:00, click the tray icon and select "Pair Phone" again for a fresh code.
   - If the phone shows *"Cannot connect to [IP]"*, ensure both devices are connected to the same Wi-Fi router.

---

### Step 1: Optional Direct Wi-Fi Download to Phone
If you ever want to install or update the app on your phone directly from your laptop without USB:
1. In the PC pairing window, click the tab **📱 Step 1: Download App**.
2. Scan the QR code with your phone camera or browser.
3. The APK (`UniversalClipboard.apk`) will download directly from your laptop over local Wi-Fi without needing internet or GitHub!

---

## Step 8: Test Text Synchronization in Both Directions

### Test 8A: PC ➔ Phone
1. On your PC, highlight this text and press `Ctrl + C`:
   `Test clipboard sync from PC to phone: 123`
2. Pick up your phone, open any text field (Notes, Search, or Chat), and long-press **Paste**.
   - **Pass**: The exact text pastes on your phone.

### Test 8B: Phone ➔ PC (Zero-Tap Seamless Auto-Sync)
To copy from your phone and paste on your PC **without ever opening the app or tapping anything**:
1. In the Universal Clipboard app on your phone, tap **`⚡ Enable Seamless Auto-Sync (Accessibility)`**.
2. Android Settings will open to Accessibility. Under *Downloaded apps* / *Installed services*, find **Universal Clipboard Auto-Sync** and toggle it **ON**.
3. Now test zero-tap sync:
   - Open **Chrome**, **WhatsApp**, or any **Notes** app on your phone.
   - Highlight any text and tap **Copy**.
   - On your PC, immediately press `Ctrl + V` in Notepad.
   - **Pass**: The copied text pastes directly onto your PC within a fraction of a second, with **zero manual taps**!

### Test 8C: Phone ➔ PC (Manual Notification / In-App Fallback)
If Accessibility is disabled, you can still sync manually:
1. Copy text on your phone.
2. Swipe down the Android Notification shade and tap **`[ 📋 Send to PC ]`** (or tap "Send Clipboard to PC" inside the app).
3. On PC, press `Ctrl + V` in Notepad.
   - **Pass**: The text pastes into Notepad.

### Test 8D: Multiline & Unicode
1. On PC, copy: `Multi-line test:\n🚀 Rocket Emoji\nSpecial chars: &<>"'`
2. Paste on phone.
   - **Pass**: Newlines and emoji paste intact.

---

## Step 9: Test Reconnecting After Restarting Desktop App

1. On your PC, right-click the Universal Clipboard tray icon and select **Quit**.
2. Wait 5 seconds.
3. Double-click `dist\UniversalClipboard.exe` again.
4. **Do NOT scan the QR code again.**
5. Observe your phone:
   - **Pass**: Within 10–15 seconds, the phone reconnects automatically and returns to the green **Connected** state.
6. Copy text on PC and paste on phone to confirm sync resumed.

---

## Step 10: Test Image Synchronization (Workflow-Dependent)

> [!NOTE]
> *Automated tests verified the image protocol and byte serialization. However, actual cross-app image pasting depends on each individual mobile app's support for image clipboard content.*

### Test 10A: PC Screenshot ➔ Phone
1. On your PC, press `Win + Shift + S` and snip a small area of your screen.
2. Wait 2 seconds.
3. On your phone, observe the notification: *"🖼️ Image copied from PC — ready to paste!"*.
4. Open an app that supports image pasting (e.g., Google Keep, WhatsApp, Slack, or Gmail draft).
5. Tap **Paste**.
   - Record whether the image pastes into your target app.

### Test 10B: Phone ➔ PC Image
1. On your phone, open your Gallery and copy an image.
2. Swipe down the notification drawer and tap **`[ 📋 Send to PC ]`**.
3. On PC, open Microsoft Paint and press `Ctrl + V`.
   - **Pass**: The image appears on the Paint canvas.

---

## Step 11: Record Results and Restore Setup If Needed

1. Open [`docs/SMOKE_TEST_RESULTS_TEMPLATE.md`](file:///c:/Users/gmura/Music/Copy%20and%20Paste/docs/SMOKE_TEST_RESULTS_TEMPLATE.md) and record your findings (PASS / FAIL / NOT SURE / NOT TESTED).
2. **If you encounter an issue**:
   - Right-click the PC tray icon and click **`📄 View Diagnostic Logs`**.
   - Notepad will open with `%APPDATA%\UniversalClipboard\universal_clipboard.log`. (All clipboard contents and secrets are redacted for privacy).
3. **If you decide to revert to your previous setup**:
   - Follow Section 4 of [`docs/SAFE_TESTING_AND_ROLLBACK.md`](file:///c:/Users/gmura/Music/Copy%20and%20Paste/docs/SAFE_TESTING_AND_ROLLBACK.md#4-safe-rollback-procedure-how-to-return-to-your-old-setup).
