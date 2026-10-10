import sys
import asyncio
import threading
import logging
import queue
import time
import socket
import signal
import io
import base64
import json
import pyperclip

try:
    from PIL import ImageGrab, Image
    IMAGE_SUPPORT = True
except ImportError:
    IMAGE_SUPPORT = False

sys.path.append('.')

from desktop.clipboard_manager import ClipboardManager
from desktop.crypto import CryptoManager, generate_key, key_from_hex
from desktop.server import WebSocketServer
from desktop.tray import TrayApp
from desktop.hotkey_manager import HotkeyManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# ── Write received content to Windows clipboard ──────────────────────────────
def write_to_windows_clipboard(clip_type: str, data: str):
    """Writes text or image data to the Windows clipboard."""
    try:
        if clip_type == 'text':
            pyperclip.copy(data)
            logger.info(f"Phone→Laptop: wrote text to clipboard ({len(data)} chars)")

        elif clip_type == 'image' and IMAGE_SUPPORT:
            img_bytes = base64.b64decode(data)
            img = Image.open(io.BytesIO(img_bytes))

            # Use win32clipboard for actual image clipboard write
            import win32clipboard
            import win32con

            output = io.BytesIO()
            img.convert('RGB').save(output, 'BMP')
            bmp_data = output.getvalue()[14:]  # strip BMP file header

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32con.CF_DIB, bmp_data)
            win32clipboard.CloseClipboard()
            logger.info("Phone→Laptop: wrote image to clipboard")

    except Exception as e:
        logger.error(f"Error writing to Windows clipboard: {e}")

# ─────────────────────────────────────────────────────────────────────────────

class AppState:
    def __init__(self):
        self.message_queue = queue.Queue()
        self.running = True
        self.auto_sync = True
        self.hotkey_mode = False
        self.last_written_hash = None  # prevent echo-back loops


def run_server_loop(server, app_state):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def server_task():
        await server.start()
        while app_state.running:
            try:
                if not app_state.message_queue.empty():
                    msg = app_state.message_queue.get()
                    await server.broadcast(msg)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in server loop: {e}")
        await server.stop()

    try:
        loop.run_until_complete(server_task())
    finally:
        loop.close()


def main():
    logger.info("Starting Universal Clipboard Sync...")

    key_hex = generate_key()
    key_bytes = key_from_hex(key_hex)
    logger.info(f"Pairing Token: {key_hex}")

    crypto_manager = CryptoManager(key_bytes)
    app_state = AppState()

    ip = get_ip()
    port = 8765

    # ── Phone→Laptop: handle incoming messages from Android ──────────────────
    def on_receive_from_phone(encrypted_payload: str):
        """Called when Android sends clipboard content to us."""
        try:
            payload = crypto_manager.decrypt(encrypted_payload)
            clip_type = payload.get('type', 'text')
            data = payload.get('data', '')

            import hashlib
            content_hash = hashlib.sha256(data.encode()).hexdigest()

            # Avoid echoing back what we just sent
            if content_hash == app_state.last_written_hash:
                return

            app_state.last_written_hash = content_hash
            write_to_windows_clipboard(clip_type, data)

        except Exception as e:
            logger.error(f"Error handling phone→laptop message: {e}")

    server = WebSocketServer(host='0.0.0.0', port=port, on_receive=on_receive_from_phone)

    server_thread = threading.Thread(target=run_server_loop, args=(server, app_state), daemon=True)
    server_thread.start()

    # ── Laptop→Phone: monitor clipboard and broadcast ────────────────────────
    def on_clipboard_change(clip_type, clip_data):
        if not app_state.auto_sync:
            return
        try:
            import hashlib
            content_hash = hashlib.sha256(clip_data.encode()).hexdigest()

            # Don't send back content that came FROM the phone
            if content_hash == app_state.last_written_hash:
                return

            app_state.last_written_hash = content_hash
            logger.info(f"Laptop→Phone: type={clip_type}, len={len(clip_data)}")
            encrypted_payload = crypto_manager.encrypt(clip_type, clip_data)
            app_state.message_queue.put(encrypted_payload)
        except Exception as e:
            logger.error(f"Error processing clipboard change: {e}")

    clipboard_manager = ClipboardManager(on_clipboard_change)
    clipboard_manager.start()

    # ── Hotkey sync (manual) ─────────────────────────────────────────────────
    tray_app_ref = [None]

    def on_hotkey_pressed():
        if not app_state.hotkey_mode:
            return
        try:
            text = pyperclip.paste()
            if not text:
                return
            encrypted_payload = crypto_manager.encrypt('text', text)
            app_state.message_queue.put(encrypted_payload)
            if tray_app_ref[0] and tray_app_ref[0].icon:
                tray_app_ref[0].icon.notify("Synced via Hotkey!", "Universal Clipboard")
        except Exception as e:
            logger.error(f"Error processing hotkey sync: {e}")

    hotkey_manager = HotkeyManager(on_hotkey_pressed)
    hotkey_manager.start()

    # ── Tray App ─────────────────────────────────────────────────────────────
    def on_auto_sync_toggle(enabled):
        app_state.auto_sync = enabled

    def on_hotkey_toggle(enabled):
        app_state.hotkey_mode = enabled

    logger.info(f"Server running at ws://{ip}:{port}/ws")

    tray_app = TrayApp(key_hex, ip, port, on_auto_sync_toggle, on_hotkey_toggle)
    tray_app_ref[0] = tray_app
    app_state.auto_sync = tray_app.auto_sync
    app_state.hotkey_mode = tray_app.hotkey_mode

    try:
        tray_app.run()
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Shutting down...")
        app_state.running = False
        clipboard_manager.stop()
        hotkey_manager.stop()
        server_thread.join(timeout=2)
        sys.exit(0)


if __name__ == "__main__":
    main()
