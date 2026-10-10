import pystray
from PIL import Image
import sys
import os
import pyperclip
import logging

def _load_icon_image() -> Image.Image:
    """Load the real app icon or fall back to a simple generated one."""
    # Paths to try (works both from source and inside the .exe bundle)
    candidates = [
        os.path.join(os.path.dirname(__file__), "assets", "icon.png"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png"),
    ]
    # PyInstaller bundles data into _MEIPASS
    if hasattr(sys, "_MEIPASS"):
        candidates.insert(0, os.path.join(sys._MEIPASS, "assets", "icon.png"))

    for path in candidates:
        if os.path.isfile(path):
            try:
                img = Image.open(path).convert("RGBA").resize((64, 64), Image.LANCZOS)
                return img
            except Exception:
                pass

    # Fallback: simple programmatic icon
    from PIL import ImageDraw
    size = 64
    img = Image.new("RGBA", (size, size), (13, 27, 42, 255))
    draw = ImageDraw.Draw(img)
    # Clipboard body
    draw.rounded_rectangle([8, 14, 56, 58], radius=4, fill=(255, 255, 255, 230))
    # Clip
    draw.rounded_rectangle([22, 10, 42, 20], radius=4, fill=(255, 255, 255, 255))
    # Lines
    for y in [32, 38, 44]:
        draw.rectangle([14, y - 1, 50, y + 1], fill=(160, 170, 195, 255))
    # Bolt circle
    draw.ellipse([38, 38, 58, 58], fill=(0, 30, 60, 220))
    # Bolt shape
    bolt = [(48, 40), (44, 49), (48, 49), (44, 58), (52, 47), (48, 47)]
    draw.polygon(bolt, fill=(0, 212, 255, 255))
    return img


class TrayApp:
    def __init__(self, pairing_token, ip_address, port,
                 on_auto_sync_toggle, on_hotkey_toggle):
        self.pairing_token = pairing_token
        self.ip_address = ip_address
        self.port = port
        self.icon = None
        self.logger = logging.getLogger(__name__)

        # Default state
        self.auto_sync = True
        self.hotkey_mode = False

        self.on_auto_sync_toggle = on_auto_sync_toggle
        self.on_hotkey_toggle = on_hotkey_toggle

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

    def run(self):
        icon_image = _load_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem("Universal Clipboard", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(f"IP: {self.ip_address}", lambda: None, enabled=False),
            pystray.MenuItem(f"Port: {self.port}", lambda: None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Auto Sync", self.toggle_auto_sync, checked=lambda item: self.auto_sync),
            pystray.MenuItem("Hotkey  (Ctrl+Shift+C)", self.toggle_hotkey_mode, checked=lambda item: self.hotkey_mode),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Copy Pairing Token", self.copy_token),
            pystray.MenuItem("Quit", self.quit_app)
        )
        self.icon = pystray.Icon("Universal Clipboard", icon_image, "Universal Clipboard", menu)
        self.logger.info("Starting Tray App with custom icon...")
        self.icon.run()

    def copy_token(self):
        pyperclip.copy(self.pairing_token)
        self.icon.notify("Pairing token copied!", "Universal Clipboard")
        self.logger.info("Pairing token copied to clipboard.")

    def quit_app(self):
        self.logger.info("Quitting Tray App...")
        self.icon.stop()
        sys.exit(0)
