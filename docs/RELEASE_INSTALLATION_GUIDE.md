# Universal Clipboard Sync — Release Installation Guide

Welcome to **Universal Clipboard Sync v1.1.0**! This guide walks you through installing and configuring both the Windows application and the Android app in a few simple steps.

---

## 💻 1. Windows Installation

Choose either the **Recommended Installer** or the **Portable Version**:

### Option A: Recommended Installer (`UniversalClipboard-Setup-1.1.0.exe`)
1. Download `UniversalClipboard-Setup-1.1.0.exe`.
2. Double-click the downloaded file to run the setup wizard.
   > **Note on Windows SmartScreen**: If Windows displays *"Windows protected your PC"*, click **More info** and then click **Run anyway**. (This appears because the application is an independent open-source release without a commercial enterprise code-signing certificate).
3. Follow the wizard prompts to install. By default, it installs to your local user folder without requiring administrator privileges.
4. Check **Create a desktop icon** if desired, then click **Finish** to launch.
5. The application will appear with an icon in your Windows System Tray (near the clock).

### Option B: Portable Version (`UniversalClipboard-Portable-1.1.0.exe`)
1. Download `UniversalClipboard-Portable-1.1.0.exe`.
2. Move it to any folder of your choice (e.g., `Documents` or `Desktop`).
3. Double-click to run immediately without any installation.

---

## 📱 2. Android Installation

### Step 1: Download the APK
You can get the Android app in two ways:
- **Direct from your PC**: Open the Windows app, click the **Download APK** tab, and scan the QR code with your phone camera or visit `http://<your-pc-ip>:8765/download` in your phone browser.
- **Direct from GitHub**: Download `UniversalClipboard-Android-1.1.0.apk` from the official [GitHub Releases page](https://github.com/Jow75/universal-clipboard-sync/releases/latest).

### Step 2: Install the APK
1. Open your phone's **Downloads** or File Manager and tap `UniversalClipboard-Android-1.1.0.apk`.
2. If prompted that your browser or file manager isn't allowed to install apps:
   - Tap **Settings** in the popup.
   - Toggle **Allow from this source** to ON.
   - Press the Back button and tap **Install**.
3. Once installation completes, tap **Open**.

---

## 🔗 3. Pairing Windows & Android

1. **Connect to the same Wi-Fi**: Make sure your Windows PC and Android phone are connected to the same local Wi-Fi network.
2. **Open the Windows Pairing Window**:
   - Double-click the Universal Clipboard icon in the Windows System Tray, or right-click and select **🖥️ Open Status Window**.
   - You will see the **Pair Device (QR Code)** tab showing a pairing QR code.
3. **Scan on Android**:
   - Open the Universal Clipboard app on Android.
   - Tap **Scan QR Code**.
   - Point your phone camera at the QR code on your Windows screen.
4. **Connected!**:
   - As soon as the phone scans the QR code, the Windows status window immediately transitions to the **Connected View**:
     - 🟢 **CONNECTED TO ANDROID**
     - Device Name: e.g. *Galaxy S24* or *Pixel 8*
     - Last Sync: *Just now*
   - The phone displays **Connected to PC**.
   - **Pairing is now permanently saved!** You do not need to scan the QR code again when you reboot or reconnect to Wi-Fi.

---

## 📋 4. How to Use Clipboard Sync

### Windows ➔ Android (PC to Phone)
1. On your Windows PC, copy any text (press `Ctrl + C`).
2. Open any app on your phone (like Notes, WhatsApp, or Messages).
3. Long-press in any text field and tap **Paste**.
4. The text copied on Windows is immediately pasted on your phone!

### Android ➔ Windows (Phone to PC)
Because Android 10+ restricts background apps from silently reading clipboard data, Universal Clipboard provides two convenient options:

#### Mode 1: Seamless Zero-Tap Sync (Recommended)
1. Open **Android Settings** > **Accessibility** > **Installed Services** (or **Downloaded Apps**).
2. Tap **Universal Clipboard Sync** and toggle it **ON**.
3. Allow the requested permission.
4. **Done!** Whenever you select text in any app on your phone and tap **Copy**, the text is automatically sent to Windows in the background. Press `Ctrl + V` on your PC to paste immediately!

#### Mode 2: Notification Action (No Accessibility Needed)
If you prefer not to enable Accessibility:
1. Copy any text on your phone.
2. Swipe down your Android notification shade.
3. Tap the **📋 Send to PC** button on the Universal Clipboard notification.
4. The text is immediately sent to your PC! Press `Ctrl + V` on Windows to paste.

---

## ❓ Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **Phone can't find PC** | Firewalls or different networks | Ensure PC and Phone are on the same Wi-Fi. If prompted by Windows Defender Firewall, allow Universal Clipboard on Private networks. |
| **Phone disconnected** | Wi-Fi changed or PC went to sleep | The app automatically reconnects with exponential backoff. Once both are back online, sync resumes automatically without re-pairing. |
| **Old QR code displayed** | Stale session | Click **🔄 Refresh QR Code** in the Windows status window. |
| **Want to pair a new device** | Previous phone linked | Click **Unpair Device** in the Windows status window. |
