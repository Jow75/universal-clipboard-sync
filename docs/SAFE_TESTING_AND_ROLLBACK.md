# Safe Testing & Rollback Guide

This guide ensures your existing Universal Clipboard Sync setup, saved configurations, and device pairings remain completely safe and protected during testing of the new build.

---

## 1. How the New Build Interacts with Your Existing Setup

| Item | Your Existing Application | Newly Built Version | Risk & Coexistence Rules |
| :--- | :--- | :--- | :--- |
| **Location on PC** | Ran directly via `python desktop/main.py` (or custom shortcut) | Standalone portable executable: `C:\Users\gmura\Music\Copy and Paste\dist\UniversalClipboard.exe` | **Separate files**: The new `.exe` does not overwrite your old source files, scripts, or Python packages. |
| **Windows Installation** | Not registered in Windows "Installed Apps" (script-based) | Portable executable (no installer, no registry entry) | **No conflict in Windows Programs**: Neither modifies system-wide program registrations. |
| **Configuration Path** | Old version was **in-memory only** (generated an ephemeral token in RAM on each launch; never wrote to disk) | `%APPDATA%\UniversalClipboard\config.json` (protected with Windows DPAPI) | **Completely isolated**: Because the old version never used `APPDATA`, the new version will not overwrite any prior config. |
| **Network Ports** | TCP `8765` (WebSocket server) | TCP `8765` (WebSocket), UDP `8766` (Beacon discovery) | **Port Conflict**: You **cannot run both at the same time**. You must close your old desktop app before starting the new `.exe`. |
| **Android Application** | Installed on phone as `com.example.universalclipboard` (Protocol v1) | Build output: `app-debug.apk` (`com.example.universalclipboard`, Protocol v2) | **Package ID match & Signature Check**: Android will check if both APKs share the same signing key. If they differ, Android prevents in-place update. See Section 3. |
| **Protocol Compatibility** | Protocol v1 (unencrypted or static manual token) | Protocol v2 (HMAC-SHA256 handshake + AES-256-GCM + QR token) | **Incompatible**: The old Android app cannot connect to the new Windows app. Both devices must run the new build. |

---

## 2. Step-by-Step Backup Procedure (Do This Before Testing)

Run this non-destructive PowerShell script. It copies your configuration without modifying or deleting anything.

### Copy and Paste into PowerShell:
```powershell
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$appDataDir = "$env:APPDATA\UniversalClipboard"
$backupDir = "$env:USERPROFILE\Desktop\UniversalClipboard_Backup_$timestamp"

if (Test-Path $appDataDir) {
    # 1. Inspect existing files
    $sourceFiles = Get-ChildItem -Path $appDataDir -File
    Write-Host "Found existing configuration directory with $($sourceFiles.Count) file(s)." -ForegroundColor Cyan
    $sourceFiles | Select-Object Name, Length | Format-Table -AutoSize

    # 2. Copy non-destructively to a new timestamped folder on Desktop
    Copy-Item -Path $appDataDir -Destination $backupDir -Recurse

    # 3. Confirm backup succeeded
    if (Test-Path $backupDir) {
        $backupFiles = Get-ChildItem -Path $backupDir -File
        Write-Host "✅ Backup verified at: $backupDir" -ForegroundColor Green
        Write-Host "Backed-up files:" -ForegroundColor Green
        $backupFiles | Select-Object Name, Length | Format-Table -AutoSize
    } else {
        Write-Error "❌ Backup verification failed: $backupDir was not created."
    }
} else {
    Write-Host "ℹ️ No %APPDATA%\UniversalClipboard folder exists yet on this computer." -ForegroundColor Yellow
    Write-Host "This is completely normal: the earlier version of the app operated in-memory only." -ForegroundColor Yellow
    Write-Host "Your system has no existing config file to protect. You are safe to proceed!" -ForegroundColor Green
}
```

### Safety Guarantees:
1. **Never overwrites earlier backups**: Each run uses a fresh timestamp (`yyyyMMdd_HHmmss`).
2. **Never displays secrets**: Only file names and sizes are shown; keys and tokens are never printed.
3. **DPAPI compatibility**: Windows DPAPI encryption is tied to your Windows user account on this computer. Restoring this backup on the same Windows account will decrypt your keys with 100% fidelity.

---

## 3. Protecting Your Android Phone Setup

### Understanding the Android App Situation
1. **Same Package ID**: Both the old and new Android apps use `com.example.universalclipboard`. Android treats them as the same app.
2. **Signature Verification**: Android requires updates to be signed by the exact same developer certificate as the installed version:
   - **Case A (In-Place Update)**: If your existing phone app was built with the debug keystore on this computer, Android will update it in-place when you tap `app-debug.apk`. All permissions and data are kept.
   - **Case B (Signature Mismatch)**: If the app currently on your phone was signed with a different key, Android will block the update and display:
     `"App not installed as package conflicts with an existing package"`.
3. **What to do if Android blocks the update**:
   - If Android shows a signature conflict, **press Cancel or Done**.
   - **Do NOT uninstall the old app** at this stage.
   - A signature mismatch indicates the app on your phone was signed with a different key than this computer's debug keystore. Keep your working app intact and report this result for investigation.

---

## 4. Safe Rollback Procedure (How to Return to Your Old Setup)

If you test the new version and decide to revert to your previous setup, follow these exact steps. **This procedure never deletes any test data automatically.**

### Step 1: Stop the New Windows Executable
1. In your Windows System Tray (bottom-right near the clock), right-click the **Universal Clipboard** lightning icon and select **Quit**.
2. To confirm in PowerShell:
   ```powershell
   Get-Process UniversalClipboard -ErrorAction SilentlyContinue
   ```
   *(A blank response confirms it is completely stopped).*

### Step 2: Archive Test Configuration (Non-Destructive)
Instead of deleting your test data, move it into an archive folder so nothing is lost:
```powershell
$appDataDir = "$env:APPDATA\UniversalClipboard"
$archiveTimestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archiveDir = "$env:APPDATA\UniversalClipboard_TestArchive_$archiveTimestamp"

if (Test-Path $appDataDir) {
    Move-Item -Path $appDataDir -Destination $archiveDir
    Write-Host "✅ Test configuration safely archived to: $archiveDir" -ForegroundColor Green
}
```

### Step 3: Restore From Your Backup (If One Existed)
If you made a backup in Section 2, restore it by running:
```powershell
# Find your latest backup on Desktop
$latestBackup = Get-ChildItem "$env:USERPROFILE\Desktop" -Directory -Filter "UniversalClipboard_Backup_*" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($latestBackup) {
    Copy-Item -Path $latestBackup.FullName -Destination "$env:APPDATA\UniversalClipboard" -Recurse
    Write-Host "✅ Restored configuration from: $($latestBackup.FullName)" -ForegroundColor Green
    Get-ChildItem "$env:APPDATA\UniversalClipboard" | Select-Object Name, Length | Format-Table -AutoSize
} else {
    Write-Host "ℹ️ No Desktop backup found. Since the old application was in-memory only, no config file is required." -ForegroundColor Cyan
}
```

### Step 4: Resume Your Old Application
- If you ran your old app via Python:
  Open a command prompt in the project directory and run:
  ```powershell
  python desktop/main.py
  ```
- If you had a shortcut to your previous application, launch it as you did before.
