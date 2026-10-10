"""
Universal Clipboard — Desktop Composition Root & Coordinator
Initializes configuration, secure WebSocket server, clipboard monitor,
global hotkey hook, UDP discovery beacon, QR pairing, and tray UI.
"""
import sys
import os
import asyncio
import threading
import logging
import queue
import time
import io
import base64
import json
import pyperclip

try:
    from PIL import ImageGrab, Image
    IMAGE_SUPPORT = True
except ImportError:
    IMAGE_SUPPORT = False

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from desktop.clipboard_manager import ClipboardManager
from desktop.crypto import CryptoManager, key_from_hex
from desktop.server import SecureWebSocketServer
from desktop.tray import TrayApp
from desktop.hotkey_manager import HotkeyManager
from desktop.config import get_or_create_config, save_config, regenerate_master_key
from desktop.network_discovery import get_best_local_ip, DiscoveryBeacon
from desktop.pairing import PairingSession, PairingWindow
from desktop.protocol import (
    build_clipboard_payload,
    parse_clipboard_payload,
    compute_content_hash,
    PROTOCOL_VERSION
)

LOG_DIR = os.path.join(os.getenv('APPDATA', '.'), 'UniversalClipboard')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOG_DIR, 'universal_clipboard.log')

file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, stream_handler]
)
logger = logging.getLogger(__name__)


def write_to_windows_clipboard(clip_type: str, data: str):
    """Writes text or image data to the Windows clipboard."""
    try:
        if clip_type == 'text':
            pyperclip.copy(data)
            logger.info(f"Phone→Laptop: wrote text to clipboard ({len(data)} chars)")

        elif clip_type == 'image' and IMAGE_SUPPORT:
            img_bytes = base64.b64decode(data)
            img = Image.open(io.BytesIO(img_bytes))

            # Use win32clipboard for raw DIB bitmap write on Windows
            try:
                import win32clipboard
                import win32con

                output = io.BytesIO()
                img.convert('RGB').save(output, 'BMP')
                bmp_data = output.getvalue()[14:]  # strip 14-byte BITMAPFILEHEADER

                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_DIB, bmp_data)
                win32clipboard.CloseClipboard()
                logger.info("Phone→Laptop: wrote image to Windows clipboard")
            except Exception as w32_err:
                logger.warning(f"Win32 clipboard write fallback: {w32_err}")

    except Exception as e:
        logger.error(f"Error writing to Windows clipboard: {e}")


class AppState:
    def __init__(self):
        self.message_queue = queue.Queue()
        self.running = True
        self.auto_sync = True
        self.hotkey_mode = False
        # LRU hash tracker: {hash: timestamp} to prevent echo loops
        self.suppressed_hashes = {}
        self.lock = threading.Lock()

    def record_received_hash(self, content_hash: str):
        """Records a hash received from phone to suppress immediate echo back."""
        with self.lock:
            now = time.time()
            self.suppressed_hashes[content_hash] = now
            # Clean entries older than 60 seconds
            stale = [h for h, t in self.suppressed_hashes.items() if now - t > 60]
            for h in stale:
                del self.suppressed_hashes[h]

    def is_suppressed(self, content_hash: str) -> bool:
        """Returns True if the content hash was recently received from phone."""
        with self.lock:
            now = time.time()
            if content_hash in self.suppressed_hashes:
                if now - self.suppressed_hashes[content_hash] < 60:
                    return True
                else:
                    del self.suppressed_hashes[content_hash]
            return False


def run_server_loop(server: SecureWebSocketServer, app_state: AppState):
    """Runs aiohttp event loop in a dedicated background daemon thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def server_task():
        await server.start()
        while app_state.running:
            try:
                if not app_state.message_queue.empty():
                    msg = app_state.message_queue.get()
                    await server.broadcast(msg)
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.error(f"Error in server task loop: {e}")
        await server.stop()

    try:
        loop.run_until_complete(server_task())
    finally:
        loop.close()


def main():
    logger.info("Starting Universal Clipboard Sync...")

    # 1. Load persistent configuration
    cfg = get_or_create_config()
    server_id = cfg["device_id"]
    server_name = cfg["device_name"]
    master_key_hex = cfg["master_key_hex"]
    master_key_bytes = key_from_hex(master_key_hex)
    port = cfg.get("port", 8765)
    ip = get_best_local_ip()

    logger.info(f"Workstation ID: {server_id}")
    logger.info(f"Host: {server_name} on {ip}:{port}")

    crypto_manager = CryptoManager(master_key_bytes)
    app_state = AppState()
    app_state.auto_sync = cfg.get("auto_sync", True)
    app_state.hotkey_mode = cfg.get("hotkey_mode", False)

    tray_app_ref = [None]
    pairing_window_ref = [None]

    # 2. Callback when Android sends clipboard content to Windows
    def on_receive_from_phone(encrypted_payload: str):
        try:
            payload_dict = crypto_manager.decrypt(encrypted_payload)
            msg_type = payload_dict.get("type")

            # Check if this is a QR pairing completion handshake message
            if msg_type == "pair_request":
                # Android requesting master key over authenticated QR session
                client_id = payload_dict.get("client_id", "unknown")
                client_name = payload_dict.get("client_name", "Android Phone")
                logger.info(f"Completing pairing for: {client_name} ({client_id})")

                # Send encrypted master key to Android
                resp_payload = {
                    "v": PROTOCOL_VERSION,
                    "type": "pair_response",
                    "master_key": master_key_hex,
                    "server_id": server_id,
                    "server_name": server_name
                }
                enc_resp = crypto_manager.encrypt(resp_payload)
                app_state.message_queue.put(enc_resp)

                if pairing_window_ref[0]:
                    pairing_window_ref[0].close()
                if tray_app_ref[0]:
                    tray_app_ref[0].notify(f"Phone paired successfully: {client_name}")
                return

            clip_type, data, content_hash = parse_clipboard_payload(payload_dict)

            # Record hash to suppress reflection loop
            app_state.record_received_hash(content_hash)
            write_to_windows_clipboard(clip_type, data)

            if tray_app_ref[0]:
                preview = data[:30] + "..." if len(data) > 30 else data
                label = "image" if clip_type == "image" else f'"{preview}"'
                tray_app_ref[0].notify(f"Received {label} from phone")

        except Exception as e:
            logger.error(f"Error handling phone→laptop message: {e}")

    # 3. Client lifecycle callbacks
    def on_client_connected(client_id, client_name):
        logger.info(f"Client authenticated: {client_name} ({client_id})")
        if pairing_window_ref[0]:
            try:
                pairing_window_ref[0].close()
            except Exception as e:
                logger.debug(f"Error closing pairing window on connect: {e}")
            pairing_window_ref[0] = None

        if tray_app_ref[0]:
            count = len(server.authenticated_clients)
            tray_app_ref[0].update_connected_count(count)
            tray_app_ref[0].notify(f"Phone connected: {client_name}")

    def on_client_disconnected(client_id):
        logger.info(f"Client disconnected: {client_id}")
        if tray_app_ref[0]:
            count = len(server.authenticated_clients)
            tray_app_ref[0].update_connected_count(count)

    # 4. Instantiate server and start network thread
    server = SecureWebSocketServer(
        host='0.0.0.0',
        port=port,
        master_key_bytes=master_key_bytes,
        server_id=server_id,
        server_name=server_name,
        on_receive=on_receive_from_phone,
        on_client_connected=on_client_connected,
        on_client_disconnected=on_client_disconnected
    )

    server_thread = threading.Thread(target=run_server_loop, args=(server, app_state), daemon=True)
    server_thread.start()

    # 5. Start UDP discovery beacon
    beacon = DiscoveryBeacon(device_name=server_name, device_id=server_id, server_port=port)
    beacon.start()

    # 6. Windows clipboard monitoring (Laptop → Phone)
    def on_clipboard_change(clip_type, clip_data):
        if not app_state.auto_sync:
            return
        try:
            content_hash = compute_content_hash(clip_type, clip_data)
            # Suppress echoing back content that was received from phone
            if app_state.is_suppressed(content_hash):
                return

            logger.info(f"Laptop→Phone: broadcasting {clip_type} (hash={content_hash[:8]}...)")
            payload = build_clipboard_payload(clip_type, clip_data, source_id=server_id)
            encrypted = crypto_manager.encrypt(payload)
            app_state.message_queue.put(encrypted)
        except Exception as e:
            logger.error(f"Error processing clipboard change: {e}")

    clipboard_manager = ClipboardManager(on_clipboard_change)
    clipboard_manager.start()

    # 7. Global hotkey handler (Ctrl+Shift+C)
    def on_hotkey_pressed():
        if not app_state.hotkey_mode:
            return
        try:
            text = pyperclip.paste()
            if not text:
                return
            logger.info("Manual sync triggered via hotkey Ctrl+Shift+C")
            payload = build_clipboard_payload("text", text, source_id=server_id)
            encrypted = crypto_manager.encrypt(payload)
            app_state.message_queue.put(encrypted)
            if tray_app_ref[0]:
                tray_app_ref[0].notify("Clipboard synced via Hotkey!")
        except Exception as e:
            logger.error(f"Error processing hotkey sync: {e}")

    hotkey_manager = HotkeyManager(on_hotkey_pressed)
    hotkey_manager.start()

    # 8. QR Pairing Trigger
    def on_pair_click():
        current_ip = get_best_local_ip()
        session = PairingSession(
            ip=current_ip,
            port=port,
            server_name=server_name,
            server_id=server_id,
            master_key_hex=master_key_hex
        )
        server.set_active_pairing_session({
            "id": session.session_id,
            "token_bytes": session.token_bytes,
            "exp": session.expires_at
        })

        def run_gui():
            win = PairingWindow(session, on_cancel=lambda: server.clear_active_pairing_session())
            pairing_window_ref[0] = win
            win.show()

        gui_thread = threading.Thread(target=run_gui, daemon=True)
        gui_thread.start()

    # 9. Unpair All Devices Trigger
    def on_unpair_click():
        nonlocal master_key_hex, master_key_bytes, crypto_manager
        new_key = regenerate_master_key()
        master_key_hex = new_key
        master_key_bytes = key_from_hex(new_key)
        crypto_manager = CryptoManager(master_key_bytes)
        server.set_master_key(master_key_bytes)
        logger.info("Regenerated master key. Existing phone pairings revoked.")

    # 10. Tray App Setup
    def on_auto_sync_toggle(enabled):
        app_state.auto_sync = enabled
        cfg["auto_sync"] = enabled
        save_config(cfg)

    def on_hotkey_toggle(enabled):
        app_state.hotkey_mode = enabled
        cfg["hotkey_mode"] = enabled
        save_config(cfg)

    tray_app = TrayApp(
        ip_address=ip,
        port=port,
        on_auto_sync_toggle=on_auto_sync_toggle,
        on_hotkey_toggle=on_hotkey_toggle,
        on_pair_click=on_pair_click,
        on_unpair_click=on_unpair_click
    )
    tray_app_ref[0] = tray_app

    logger.info(f"Universal Clipboard Desktop is ready in system tray.")

    try:
        tray_app.run()
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Shutting down Universal Clipboard...")
        app_state.running = False
        beacon.stop()
        clipboard_manager.stop()
        hotkey_manager.stop()
        server_thread.join(timeout=2.0)
        sys.exit(0)


if __name__ == "__main__":
    main()
