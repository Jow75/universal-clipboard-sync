"""
Universal Clipboard — QR Pairing Manager & Desktop Pairing Dialog
Creates ephemeral, short-lived QR pairing sessions and renders
a clean pairing window with countdown timer and instructions.
"""
import os
import time
import uuid
import json
import logging
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import qrcode

logger = logging.getLogger(__name__)

QR_SESSION_TTL_SECONDS = 180  # 3 minutes


class PairingSession:
    def __init__(self, ip: str, port: int, server_name: str, server_id: str, master_key_hex: str):
        self.session_id = str(uuid.uuid4())
        self.ephemeral_token = os.urandom(32).hex()
        self.expires_at = int(time.time()) + QR_SESSION_TTL_SECONDS
        self.ip = ip
        self.port = port
        self.server_name = server_name
        self.server_id = server_id
        self.master_key_hex = master_key_hex
        self.is_completed = False
        self.is_cancelled = False

    @property
    def token_bytes(self) -> bytes:
        return bytes.fromhex(self.ephemeral_token)

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def to_qr_payload_string(self) -> str:
        """Returns compact JSON string formatted for QR encoding."""
        payload = {
            "v": 2,
            "action": "pair",
            "sid": self.session_id,
            "ip": self.ip,
            "port": self.port,
            "token": self.ephemeral_token,
            "exp": self.expires_at,
            "name": self.server_name,
            "id": self.server_id
        }
        return json.dumps(payload, separators=(',', ':'))

    def generate_qr_image(self, box_size: int = 8, border: int = 2) -> Image.Image:
        """Renders QR code as a PIL Image."""
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=box_size,
            border=border,
        )
        qr.add_data(self.to_qr_payload_string())
        qr.make(fit=True)
        return qr.make_image(fill_color="#0D1B2A", back_color="#FFFFFF").convert("RGBA")


class PairingWindow:
    """Displays desktop GUI window supporting the two-QR onboarding experience:
    1. App Download QR (Direct local Wi-Fi download from desktop)
    2. Ephemeral Device Pairing QR (with countdown timer)
    """

    def __init__(self, session: PairingSession, on_cancel=None):
        self.session = session
        self.on_cancel = on_cancel
        self.download_url = f"http://{session.ip}:{session.port}/download"
        self.root = None
        self.timer_label = None
        self.pair_photo_img = None
        self.download_photo_img = None
        self.pair_frame = None
        self.download_frame = None
        self.btn_tab_pair = None
        self.btn_tab_download = None

    def show(self):
        """Runs the dialog in the current or dedicated GUI thread."""
        self.root = tk.Toplevel() if tk._default_root else tk.Tk()
        self.root.title("Universal Clipboard — Connect & Pair")
        self.root.geometry("450x640")
        self.root.resizable(False, False)
        self.root.configure(bg="#0D1B2A")

        # Bring window to front
        self.root.attributes("-topmost", True)
        self.root.after_idle(self.root.attributes, "-topmost", False)

        # Tab Navigation Header
        tab_nav_frame = tk.Frame(self.root, bg="#1A2A3E", padx=4, pady=4)
        tab_nav_frame.pack(fill="x", padx=16, pady=(16, 8))

        self.btn_tab_pair = tk.Button(
            tab_nav_frame, text="🔗 Step 2: Pair Device",
            font=("Segoe UI", 10, "bold"), fg="#FFFFFF", bg="#0066CC",
            activebackground="#0055AA", activeforeground="#FFFFFF",
            bd=0, padx=12, pady=6, cursor="hand2",
            command=self._show_pair_tab
        )
        self.btn_tab_pair.pack(side="left", expand=True, fill="x", padx=2)

        self.btn_tab_download = tk.Button(
            tab_nav_frame, text="📱 Step 1: Download App",
            font=("Segoe UI", 10, "bold"), fg="#7B8FA8", bg="#1A2A3E",
            activebackground="#243750", activeforeground="#FFFFFF",
            bd=0, padx=12, pady=6, cursor="hand2",
            command=self._show_download_tab
        )
        self.btn_tab_download.pack(side="right", expand=True, fill="x", padx=2)

        # Main Container
        self.pair_frame = tk.Frame(self.root, bg="#0D1B2A")
        self.download_frame = tk.Frame(self.root, bg="#0D1B2A")

        self._build_pair_tab()
        self._build_download_tab()

        # Start with Pairing Tab active
        self._show_pair_tab()

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._update_countdown()
        if not tk._default_root or self.root == tk._default_root:
            self.root.mainloop()

    def _show_pair_tab(self):
        self.download_frame.pack_forget()
        self.pair_frame.pack(fill="both", expand=True)
        self.btn_tab_pair.configure(bg="#0066CC", fg="#FFFFFF")
        self.btn_tab_download.configure(bg="#1A2A3E", fg="#7B8FA8")

    def _show_download_tab(self):
        self.pair_frame.pack_forget()
        self.download_frame.pack(fill="both", expand=True)
        self.btn_tab_download.configure(bg="#0066CC", fg="#FFFFFF")
        self.btn_tab_pair.configure(bg="#1A2A3E", fg="#7B8FA8")

    def _build_pair_tab(self):
        # Title Frame
        title_frame = tk.Frame(self.pair_frame, bg="#0D1B2A")
        title_frame.pack(pady=(12, 4))

        lbl_title = tk.Label(
            title_frame, text="Pair Your Phone",
            font=("Segoe UI", 16, "bold"), fg="#FFFFFF", bg="#0D1B2A"
        )
        lbl_title.pack()

        lbl_sub = tk.Label(
            title_frame,
            text="Open Universal Clipboard on phone and tap 'Scan QR Code'",
            font=("Segoe UI", 9), fg="#7B8FA8", bg="#0D1B2A", wraplength=380
        )
        lbl_sub.pack(pady=(2, 0))

        # QR Code Container
        qr_frame = tk.Frame(self.pair_frame, bg="#FFFFFF", padx=10, pady=10, bd=0)
        qr_frame.pack(pady=12)

        qr_pil_img = self.session.generate_qr_image(box_size=6, border=2)
        self.pair_photo_img = ImageTk.PhotoImage(qr_pil_img)
        lbl_qr = tk.Label(qr_frame, image=self.pair_photo_img, bg="#FFFFFF")
        lbl_qr.pack()

        # Connection detail pill
        info_frame = tk.Frame(self.pair_frame, bg="#1A2A3E", padx=12, pady=6)
        info_frame.pack(pady=4)

        lbl_ip = tk.Label(
            info_frame, text=f"Computer: {self.session.server_name} ({self.session.ip})",
            font=("Segoe UI", 9, "bold"), fg="#00DD88", bg="#1A2A3E"
        )
        lbl_ip.pack()

        # Countdown Timer Label
        self.timer_label = tk.Label(
            self.pair_frame, text="", font=("Segoe UI", 10), fg="#FFAA00", bg="#0D1B2A"
        )
        self.timer_label.pack(pady=(6, 12))

        # Cancel Button
        btn_cancel = tk.Button(
            self.pair_frame, text="Cancel", font=("Segoe UI", 10, "bold"),
            fg="#FFFFFF", bg="#CC2244", activebackground="#AA1133",
            activeforeground="#FFFFFF", bd=0, padx=20, pady=6,
            cursor="hand2", command=self.close
        )
        btn_cancel.pack(pady=(0, 12))

    def _build_download_tab(self):
        title_frame = tk.Frame(self.download_frame, bg="#0D1B2A")
        title_frame.pack(pady=(12, 4))

        lbl_title = tk.Label(
            title_frame, text="Download Mobile App",
            font=("Segoe UI", 16, "bold"), fg="#FFFFFF", bg="#0D1B2A"
        )
        lbl_title.pack()

        lbl_sub = tk.Label(
            title_frame,
            text="Scan with your phone's standard camera to download the APK",
            font=("Segoe UI", 9), fg="#7B8FA8", bg="#0D1B2A", wraplength=380
        )
        lbl_sub.pack(pady=(2, 0))

        # QR Code Container for Download Link
        qr_frame = tk.Frame(self.download_frame, bg="#FFFFFF", padx=10, pady=10, bd=0)
        qr_frame.pack(pady=12)

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(self.download_url)
        qr.make(fit=True)
        download_qr_img = qr.make_image(fill_color="#003366", back_color="#FFFFFF").convert("RGBA")
        self.download_photo_img = ImageTk.PhotoImage(download_qr_img)

        lbl_qr = tk.Label(qr_frame, image=self.download_photo_img, bg="#FFFFFF")
        lbl_qr.pack()

        # Instructions Frame
        inst_frame = tk.Frame(self.download_frame, bg="#1A2A3E", padx=12, pady=8)
        inst_frame.pack(pady=6, padx=24, fill="x")

        lbl_inst = tk.Label(
            inst_frame,
            text=f"1. Scan with phone's camera to download APK directly from PC.\n"
                 f"2. URL: {self.download_url}\n"
                 f"3. Install APK, open app, then switch to 'Step 2: Pair Device'.",
            font=("Segoe UI", 9), fg="#CCD8E8", bg="#1A2A3E", justify="left"
        )
        lbl_inst.pack()

        # Switch to Pair Button
        btn_next = tk.Button(
            self.download_frame, text="Ready? Go to Step 2 ➔",
            font=("Segoe UI", 10, "bold"), fg="#FFFFFF", bg="#008855",
            activebackground="#006644", activeforeground="#FFFFFF",
            bd=0, padx=20, pady=6, cursor="hand2",
            command=self._show_pair_tab
        )
        btn_next.pack(pady=(8, 12))

    def _update_countdown(self):
        if not self.root or not self.root.winfo_exists():
            return
        remaining = self.session.expires_at - int(time.time())
        if remaining <= 0 or self.session.is_completed:
            if not self.session.is_completed:
                try:
                    self.timer_label.config(text="⚠️ QR code expired", fg="#FF4444")
                except Exception:
                    pass
            self.root.after(1000, self._safe_destroy)
            return

        mins = remaining // 60
        secs = remaining % 60
        try:
            self.timer_label.config(text=f"Expires in {mins:02d}:{secs:02d}")
            self.root.after(1000, self._update_countdown)
        except Exception:
            pass

    def close(self):
        """Thread-safe window close method."""
        self.session.is_cancelled = True
        if self.root and self.root.winfo_exists():
            try:
                # Schedule destruction on Tk thread to avoid Tcl_Panic / 0x80000003
                self.root.after(0, self._safe_destroy)
            except Exception as e:
                logger.debug(f"Error scheduling safe destroy: {e}")

    def _safe_destroy(self):
        """Executes strictly on Tkinter event loop thread."""
        try:
            if self.on_cancel:
                self.on_cancel()
        except Exception:
            pass
        if self.root and self.root.winfo_exists():
            try:
                self.root.quit()
                self.root.destroy()
            except Exception as e:
                logger.debug(f"Error in Tk destroy: {e}")
            self.root = None
