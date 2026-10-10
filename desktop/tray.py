import pystray
from PIL import Image, ImageDraw
import sys
import os
import pyperclip
import logging

logger = logging.getLogger(__name__)


def _load_icon_image() -> Image.Image:
    """Load the real app icon or fall back to a simple generated one."""
    candidates = [
        os.path.join(os.path.dirname(__file__), "assets", "icon.png"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png"),
    ]
    if hasattr(sys, "_MEIPASS"):
        candidates.insert(0, os.path.join(sys._MEIPASS, "desktop", "assets", "icon.png"))
        candidates.insert(1, os.path.join(sys._MEIPASS, "assets", "icon.png"))

    for path in candidates:
        if os.path.isfile(path):
            try:
                img = Image.open(path).convert("RGBA").resize((64, 64), Image.LANCZOS)
                return img
            except Exception:
                pass

    # Programmatic fallback icon
    size = 64
    img = Image.new("RGBA", (size, size), (13, 27, 42, 255))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([8, 14, 56, 58], radius=4, fill=(255, 255, 255, 230))
    draw.rounded_rectangle([22, 10, 42, 20], radius=4, fill=(255, 255, 255, 255))
    for y in [32, 38, 44]:
        draw.rectangle([14, y - 1, 50, y + 1], fill=(160, 170, 195, 255))
    draw.ellipse([38, 38, 58, 58], fill=(0, 30, 60, 220))
    bolt = [(48, 40), (44, 49), (48, 49), (44, 58), (52, 47), (48, 47)]
    draw.polygon(bolt, fill=(0, 212, 255, 255))
    return img


class TrayApp:
    def __init__(self, ip_address: str, port: int,
                 on_auto_sync_toggle, on_hotkey_toggle,
                 on_pair_click=None, on_unpair_click=None,
                 on_open_status_window=None):
        self.ip_address = ip_address
        self.port = port
        self.icon = None
        self.logger = logging.getLogger(__name__)

        self.auto_sync = True
        self.hotkey_mode = False
        self.connected_count = 0
        self.connected_device_name = "Android Phone"

        self.on_auto_sync_toggle = on_auto_sync_toggle
        self.on_hotkey_toggle = on_hotkey_toggle
        self.on_pair_click = on_pair_click
        self.on_unpair_click = on_unpair_click
        self.on_open_status_window = on_open_status_window

    def update_connected_count(self, count: int, device_name: str = None):
        self.connected_count = count
        if device_name:
            self.connected_device_name = device_name
        elif count == 0:
            self.connected_device_name = "Android Phone"
        if self.icon:
            self.icon.update_menu()

    def trigger_open_status(self, icon=None, item=None):
        if self.on_open_status_window:
            self.on_open_status_window()
        elif self.on_pair_click:
            self.on_pair_click()

    def toggle_auto_sync(self, icon, item):
        self.auto_sync = not self.auto_sync
        self.logger.info(f"Auto Sync toggled: {self.auto_sync}")
        if self.on_auto_sync_toggle:
            self.on_auto_sync_toggle(self.auto_sync)

    def toggle_hotkey_mode(self, icon, item):
        self.hotkey_mode = not self.hotkey_mode
        self.logger.info(f"Hotkey Mode toggled: {self.hotkey_mode}")
        if self.on_hotkey_toggle:
            self.on_hotkey_toggle(self.hotkey_mode)

    def trigger_pair_qr(self, icon=None, item=None):
        if self.on_pair_click:
            self.on_pair_click()

    def trigger_unpair_all(self, icon=None, item=None):
        if self.on_unpair_click:
            self.on_unpair_click()
            if self.icon:
                self.icon.notify("All paired devices have been disconnected.", "Universal Clipboard")

    def open_logs(self, icon=None, item=None):
        log_file = os.path.join(os.getenv('APPDATA', '.'), 'UniversalClipboard', 'universal_clipboard.log')
        if os.path.exists(log_file):
            try:
                os.startfile(log_file)
            except Exception as e:
                self.logger.error(f"Error opening log file: {e}")
        else:
            self.notify("No logs recorded yet.", "Universal Clipboard")

    def run(self):
        icon_image = _load_icon_image()

        def status_text(item):
            if self.connected_count > 0:
                return f"🟢 Connected: {self.connected_device_name}"
            return "⚪ Waiting for phone"

        menu = pystray.Menu(
            pystray.MenuItem("Universal Clipboard Sync", lambda: None, enabled=False),
            pystray.MenuItem(status_text, lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("🖥️ Open Status Window", self.trigger_open_status, default=True),
            pystray.MenuItem("📱 Pair Phone (QR Code)", self.trigger_pair_qr),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(f"IP: {self.ip_address}", lambda: None, enabled=False),
            pystray.MenuItem(f"Port: {self.port}", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Auto Sync", self.toggle_auto_sync, checked=lambda item: self.auto_sync),
            pystray.MenuItem("Hotkey Sync (Ctrl+Shift+C)", self.toggle_hotkey_mode, checked=lambda item: self.hotkey_mode),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("📄 View Diagnostic Logs", self.open_logs),
            pystray.MenuItem("Unpair All Devices", self.trigger_unpair_all),
            pystray.MenuItem("Quit", self.quit_app)
        )
        self.icon = pystray.Icon("Universal Clipboard", icon_image, "Universal Clipboard", menu)
        self.logger.info("Starting Tray App...")
        self.icon.run()

    def notify(self, message: str, title: str = "Universal Clipboard"):
        if self.icon:
            try:
                self.icon.notify(message, title)
            except Exception as e:
                self.logger.debug(f"Tray notify error: {e}")

    def quit_app(self, icon=None, item=None):
        self.logger.info("Quitting Tray App...")
        if self.icon:
            self.icon.stop()
        sys.exit(0)
