import hashlib
import time
import threading
import logging
import pyperclip
import io
import base64

try:
    from PIL import ImageGrab, Image
    IMAGE_SUPPORT = True
except ImportError:
    IMAGE_SUPPORT = False

class ClipboardManager:
    def __init__(self, callback):
        self.last_hash = None
        self.callback = callback
        self.debounce_time = 0.3
        self.running = False
        self.thread = None
        self.last_change_time = 0
        self.logger = logging.getLogger(__name__)

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        self.logger.info("Clipboard monitoring started.")

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.logger.info("Clipboard monitoring stopped.")

    def _get_clipboard_content(self):
        """
        Returns a tuple: (type, data)
          type = 'text' | 'image'
          data = str (for text) | base64 str (for image)
        """
        # 1. Try to grab an image from the clipboard (Windows/macOS)
        if IMAGE_SUPPORT:
            try:
                img = ImageGrab.grabclipboard()
                if isinstance(img, Image.Image):
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG')
                    b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                    return ('image', b64)
            except Exception:
                pass  # Fall through to text check

        # 2. Try text
        try:
            text = pyperclip.paste()
            if text:
                return ('text', text)
        except Exception:
            pass

        return (None, None)

    def _monitor_loop(self):
        while self.running:
            try:
                clip_type, clip_data = self._get_clipboard_content()

                if clip_type is None or clip_data is None:
                    time.sleep(0.5)
                    continue

                current_hash = hashlib.sha256(clip_data.encode('utf-8')).hexdigest()

                if current_hash != self.last_hash:
                    now = time.time()
                    if now - self.last_change_time < self.debounce_time:
                        time.sleep(0.1)
                        continue

                    self.last_hash = current_hash
                    self.last_change_time = now
                    self.logger.info(f"Clipboard change detected: type={clip_type}")

                    if self.callback:
                        self.callback(clip_type, clip_data)

            except Exception as e:
                self.logger.error(f"Error reading clipboard: {e}")

            time.sleep(0.5)
