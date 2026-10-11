# Android 13, 14 & 15 Accessibility "Restricted Setting" Resolution Guide

## 1. Executive Summary & Root Cause Analysis

When attempting to enable **Seamless Auto-Sync** on modern Android devices (Android 13, 14, and 15), users who install Universal Clipboard Sync from an APK file (via Chrome, browser download, file manager, WhatsApp, or local Wi-Fi download) may encounter the following system prompt in Android Accessibility settings:

> **"Restricted setting. For your security, this setting is currently unavailable."**

### Why Does This Occur?
Starting in Android 13 (API 33), Google introduced an intentional operating system security defense against sideloaded malware abusing Accessibility Services and Notification Listeners.

- When an application is installed via a verified app store session (e.g. Google Play Store, Samsung Galaxy Store), Android marks the package as trusted.
- When an application is **sideloaded directly from an APK**, Android flags sensitive APIs as restricted (`APP_OP_ACCESS_RESTRICTED_SETTINGS = MODE_ERRORED`).
- **This restriction is not a defect in the Universal Clipboard APK or its manifest declaration.** It is an operating system policy applied universally to all sideloaded apps requesting accessibility.

---

## 2. Official Step-by-Step Resolution

Android provides an official, device-owner-controlled override for trusted applications:

### Step 1: Open App Info for Universal Clipboard
1. Open the Universal Clipboard app and tap **"Step 1: App Info (Allow)"** on the dialog.
   - *Alternative method:* Long-press the **Universal Clipboard** app icon on your home screen or app drawer and tap the **ℹ️ (App Info)** icon.
   - *Settings method:* Open phone **Settings** → **Apps** (or **App Management**) → **Universal Clipboard**.

### Step 2: Allow Restricted Settings
1. On the **App Info** screen, look at the **top-right corner** for the **three vertical dots (⋮)** menu.
2. Tap **"Allow restricted settings"** (on some devices, labeled as *"Allow restricted access"*).
3. Android will prompt you to verify your identity. Enter your phone **PIN, pattern, or fingerprint**.
4. A system toast will confirm: *"Restricted settings allowed"*.

> **Note for Xiaomi / MIUI / HyperOS / Tecno devices:**
> On some OEM versions, this option may appear under **App Permissions** or at the bottom of the App Info page as a toggle named *"Restricted settings"*.

### Step 3: Turn On Accessibility Service
1. Return to the Universal Clipboard app and tap **"Step 2: Accessibility"**.
   - *Alternative method:* Open phone **Settings** → **Accessibility** → **Universal Clipboard Sync**.
2. Tap **Universal Clipboard Sync**.
3. Toggle the switch to **ON**.
4. When prompted by Android with the standard accessibility permission disclosure, tap **Allow**.

**Outcome:** The status in Universal Clipboard will immediately transition to:
`⚡ Seamless Auto-Sync: Active` (in green).

---

## 3. Privacy & Security Assurances

Universal Clipboard Sync requests accessibility strictly to detect clipboard copy events when other apps are focused. We provide the following architectural guarantees:

1. **No Screen Scraping**: `accessibility_service_config.xml` explicitly declares:
   ```xml
   android:canRetrieveWindowContent="false"
   ```
   The service **cannot** read your screen, inspect text fields, read passwords, or examine other applications.
2. **Local Wi-Fi Only**: Clipboard data is never uploaded to external servers or cloud services. All transmissions occur strictly between your paired phone and PC over your private home/work Wi-Fi link.
3. **No Persistent History**: Copied text is processed in transient volatile memory and is never logged to disk or tracked across restarts.
4. **Instant Revocation**: You can turn off the service at any time under **Settings → Accessibility → Universal Clipboard Sync → Off**.
