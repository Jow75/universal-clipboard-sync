# Universal Clipboard Sync

A cross-device clipboard synchronization tool. This MVP focuses on synchronizing text from Windows Desktop to Android via a local network connection.

## Architecture (MVP - Local Mode)

### Desktop App (Windows)
- **Role**: Server & Clipboard Monitor
- **Tech Stack**: Python (pyperclip, pystray, aiohttp/websockets, pynput)
- **Modules**:
  - `clipboard_manager.py`: Monitors system clipboard changes. Implements deduplication (hashing) and debounce (300ms).
  - `crypto.py`: Encrypts clipboard content using AES-GCM with a shared secret. Random IV/Nonce per message.
  - `server.py`: Runs a WebSocket server to broadcast encrypted clipboard content to connected clients (Android).
  - `tray.py`: System tray UI to show connection status, Pairing Token, and Toggles.
  - `hotkey_manager.py`: Global hotkey listener (Ctrl+Shift+C) for manual sync.
  - `main.py`: Entry point.

### Android App
- **Role**: Client
- **Tech Stack**: Kotlin (OkHttp for WebSockets)
- **Modules**:
  - `NetworkClient`: Connects to the Desktop WebSocket server with automatic reconnection.
  - `CryptoManager`: Decrypts incoming payloads using the shared secret.
  - `ClipboardHandler`: Updates the Android system clipboard.
  - `ClipboardService`: Foreground Service to keep connection alive in background.
  - `MainActivity`: UI for entering the Desktop IP and Pairing Token.

### Security
- **Encryption**: AES-GCM (256-bit key derived from Pairing Token).
- **Transport**: WebSockets over Local Network (HTTP). Payload is encrypted.
- **Pairing**: Shared secret/token manually entered on both devices.

## Usage
1.  Run the Desktop App: `python desktop/main.py`
2.  Note the displayed IP and Pairing Token (click "Copy Pairing Token" in tray).
3.  Open the Android App. Enter the IP and Token. Click Connect.
4.  Copy text on Windows. It should appear on Android clipboard.
5.  Or use `Ctrl+Shift+C` to sync manually (if Hotkey Mode is enabled).

## Toggles (Tray Menu)
- **Auto Sync**: If checked, every clipboard change is synced.
- **Hotkey Mode**: If checked, `Ctrl+Shift+C` triggers a sync.

## Future Plans
-   Cloud Sync (Firebase)
-   Image Support
-   Bi-directional Sync
