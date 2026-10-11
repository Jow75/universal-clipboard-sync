"""
Universal Clipboard — Desktop Connection & QR Pairing Manager
Renders a modern, responsive status and pairing window with:
1. Ephemeral QR Pairing with countdown timer and single-use security
2. Connected Device View with green indicator, device name, and actions
3. Local Wi-Fi & Official GitHub APK Download QR codes
4. Thread-safe event dispatching between asyncio server and Tkinter UI
"""
import os
import time
import uuid
import json
import logging
import queue
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import qrcode
from desktop.version import APP_NAME, APP_VERSION, CANONICAL_DOWNLOAD_PAGE

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

    def refresh(self):
        """Generates a fresh ephemeral token and resets timer."""
        self.session_id = str(uuid.uuid4())
        self.ephemeral_token = os.urandom(32).hex()
        self.expires_at = int(time.time()) + QR_SESSION_TTL_SECONDS
        self.is_completed = False
        self.is_cancelled = False

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

    def generate_qr_image(self, box_size: int = 7, border: int = 2) -> Image.Image:
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


class DesktopConnectionWindow:
    """Desktop status and pairing window that manages connection states:
    - WAITING_FOR_PAIRING: Displays pairing QR code and countdown
    - CONNECTED: Replaces QR with green status, device name, and sync controls
    - DOWNLOAD: Shows direct Wi-Fi & official GitHub release download links
    """

    def __init__(self, session: PairingSession, on_cancel=None, on_disconnect=None, on_refresh_session=None,
                 on_disconnect_device=None, on_remove_device=None, on_rename_device=None,
                 get_paired_devices=None, get_active_devices=None):
        self.session = session
        self.on_cancel = on_cancel
        self.on_disconnect = on_disconnect
        self.on_refresh_session = on_refresh_session
        self.on_disconnect_device = on_disconnect_device
        self.on_remove_device = on_remove_device
        self.on_rename_device = on_rename_device
        self.get_paired_devices_cb = get_paired_devices
        self.get_active_devices_cb = get_active_devices
        self.download_url = f"http://{session.ip}:{session.port}/download"
        self.canonical_download_url = CANONICAL_DOWNLOAD_PAGE

        self.root = None
        self.event_queue = queue.Queue()
        self.is_connected = False
        self.connected_device_name = "Android Phone"
        self.connected_device_id = ""
        self.last_sync_info = "Ready to sync"

        # Widget references
        self.timer_label = None
        self.pair_photo_img = None
        self.download_photo_img = None
        self.pair_frame = None
        self.connected_frame = None
        self.download_frame = None
        self.lbl_qr_pair = None
        self.connected_device_label = None
        self.last_sync_label = None
        self.btn_tab_pair = None
        self.btn_tab_connected = None
        self.btn_tab_download = None
        self.devices_list_frame = None

    def post_event(self, event_type: str, data=None):
        """Thread-safe event posting from server or other threads."""
        self.event_queue.put((event_type, data))

    def show(self):
        """Initializes and runs the window."""
        self.root = tk.Toplevel() if tk._default_root else tk.Tk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("460x660")
        self.root.resizable(False, False)
        self.root.configure(bg="#0D1B2A")

        # Bring window to front initially
        self.root.attributes("-topmost", True)
        self.root.after_idle(self.root.attributes, "-topmost", False)

        # Tab Navigation Header
        tab_nav_frame = tk.Frame(self.root, bg="#1A2A3E", padx=4, pady=4)
        tab_nav_frame.pack(fill="x", padx=16, pady=(16, 8))

        self.btn_tab_pair = tk.Button(
            tab_nav_frame, text="🔗 Pair Phone",
            font=("Segoe UI", 9, "bold"), fg="#FFFFFF", bg="#0066CC",
            activebackground="#0055AA", activeforeground="#FFFFFF",
            bd=0, padx=8, pady=6, cursor="hand2",
            command=self._show_pair_tab
        )
        self.btn_tab_pair.pack(side="left", expand=True, fill="x", padx=2)

        self.btn_tab_connected = tk.Button(
            tab_nav_frame, text="🟢 Connected",
            font=("Segoe UI", 9, "bold"), fg="#7B8FA8", bg="#1A2A3E",
            activebackground="#243750", activeforeground="#FFFFFF",
            bd=0, padx=8, pady=6, cursor="hand2",
            command=self._show_connected_tab
        )
        self.btn_tab_connected.pack(side="left", expand=True, fill="x", padx=2)

        self.btn_tab_download = tk.Button(
            tab_nav_frame, text="📱 Download App",
            font=("Segoe UI", 9, "bold"), fg="#7B8FA8", bg="#1A2A3E",
            activebackground="#243750", activeforeground="#FFFFFF",
            bd=0, padx=8, pady=6, cursor="hand2",
            command=self._show_download_tab
        )
        self.btn_tab_download.pack(side="left", expand=True, fill="x", padx=2)

        # Main Container Frames
        self.pair_frame = tk.Frame(self.root, bg="#0D1B2A")
        self.connected_frame = tk.Frame(self.root, bg="#0D1B2A")
        self.download_frame = tk.Frame(self.root, bg="#0D1B2A")

        self._build_pair_tab()
        self._build_connected_tab()
        self._build_download_tab()

        if self.is_connected:
            self._show_connected_tab()
        else:
            self._show_pair_tab()

        # Closing window minimizes to tray instead of quitting
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        # Start timer and event queue consumer loop
        self._update_countdown()
        self._process_events()

        if not tk._default_root or self.root == tk._default_root:
            self.root.mainloop()

    def _process_events(self):
        """Pulls events from thread-safe queue and updates Tk widgets."""
        if not self.root or not self.root.winfo_exists():
            return

        try:
            while not self.event_queue.empty():
                event_type, data = self.event_queue.get_nowait()
                if event_type == "client_connected":
                    client_name = data.get("name", "Android Phone") if isinstance(data, dict) else str(data)
                    self.set_connected(client_name)
                elif event_type == "client_disconnected":
                    self.set_disconnected()
                elif event_type == "sync_info":
                    self.set_sync_info(str(data))
                elif event_type == "refresh_qr":
                    self._refresh_qr_display()
        except Exception as e:
            logger.error(f"Error processing GUI event: {e}")

        self.root.after(50, self._process_events)

    def _show_pair_tab(self):
        self.connected_frame.pack_forget()
        self.download_frame.pack_forget()
        self.pair_frame.pack(fill="both", expand=True)
        self.btn_tab_pair.configure(bg="#0066CC", fg="#FFFFFF")
        self.btn_tab_connected.configure(bg="#1A2A3E", fg="#7B8FA8")
        self.btn_tab_download.configure(bg="#1A2A3E", fg="#7B8FA8")

    def _show_connected_tab(self):
        self.pair_frame.pack_forget()
        self.download_frame.pack_forget()
        self.connected_frame.pack(fill="both", expand=True)
        self.btn_tab_connected.configure(bg="#008855", fg="#FFFFFF")
        self.btn_tab_pair.configure(bg="#1A2A3E", fg="#7B8FA8")
        self.btn_tab_download.configure(bg="#1A2A3E", fg="#7B8FA8")

    def _show_download_tab(self):
        self.pair_frame.pack_forget()
        self.connected_frame.pack_forget()
        self.download_frame.pack(fill="both", expand=True)
        self.btn_tab_download.configure(bg="#0066CC", fg="#FFFFFF")
        self.btn_tab_pair.configure(bg="#1A2A3E", fg="#7B8FA8")
        self.btn_tab_connected.configure(bg="#1A2A3E", fg="#7B8FA8")

    def _build_pair_tab(self):
        title_frame = tk.Frame(self.pair_frame, bg="#0D1B2A")
        title_frame.pack(pady=(8, 2))

        lbl_title = tk.Label(
            title_frame, text="📱 Scan to Pair Phone",
            font=("Segoe UI", 15, "bold"), fg="#FFFFFF", bg="#0D1B2A"
        )
        lbl_title.pack()

        lbl_sub = tk.Label(
            title_frame,
            text="Open Universal Clipboard on phone and tap 'Scan QR Code'",
            font=("Segoe UI", 9), fg="#8EA5C0", bg="#0D1B2A", wraplength=380
        )
        lbl_sub.pack(pady=(2, 0))

        # QR Code Container
        qr_frame = tk.Frame(self.pair_frame, bg="#FFFFFF", padx=8, pady=8, bd=0)
        qr_frame.pack(pady=10)

        qr_pil_img = self.session.generate_qr_image(box_size=6, border=2)
        self.pair_photo_img = ImageTk.PhotoImage(qr_pil_img)
        self.lbl_qr_pair = tk.Label(qr_frame, image=self.pair_photo_img, bg="#FFFFFF")
        self.lbl_qr_pair.pack()

        # Connection detail pill
        info_frame = tk.Frame(self.pair_frame, bg="#1A2A3E", padx=12, pady=4)
        info_frame.pack(pady=2)

        lbl_ip = tk.Label(
            info_frame, text=f"Workstation: {self.session.server_name}  |  {self.session.ip}:{self.session.port}",
            font=("Segoe UI", 8, "bold"), fg="#00DD88", bg="#1A2A3E"
        )
        lbl_ip.pack()

        # Countdown Timer Label
        self.timer_label = tk.Label(
            self.pair_frame, text="", font=("Segoe UI", 10), fg="#FFAA00", bg="#0D1B2A"
        )
        self.timer_label.pack(pady=(4, 6))

        # Action Buttons
        btn_box = tk.Frame(self.pair_frame, bg="#0D1B2A")
        btn_box.pack(pady=4)

        btn_refresh = tk.Button(
            btn_box, text="🔄 Refresh Code", font=("Segoe UI", 9, "bold"),
            fg="#FFFFFF", bg="#204060", activebackground="#153048",
            activeforeground="#FFFFFF", bd=0, padx=12, pady=5,
            cursor="hand2", command=self.refresh_session
        )
        btn_refresh.pack(side="left", padx=4)

        btn_min = tk.Button(
            btn_box, text="Minimize to Tray", font=("Segoe UI", 9),
            fg="#CCD8E8", bg="#1A2A3E", activebackground="#243750",
            activeforeground="#FFFFFF", bd=0, padx=12, pady=5,
            cursor="hand2", command=self.hide_to_tray
        )
        btn_min.pack(side="left", padx=4)

        lbl_sec = tk.Label(
            self.pair_frame,
            text="🔒 Ephemeral pairing session expires in 3 minutes.\nMaster key is encrypted and stored in Windows DPAPI.",
            font=("Segoe UI", 8), fg="#5D738E", bg="#0D1B2A", justify="center"
        )
        lbl_sec.pack(pady=(6, 0))

    def _build_connected_tab(self):
        title_frame = tk.Frame(self.connected_frame, bg="#0D1B2A")
        title_frame.pack(pady=(12, 4))

        # Status badge
        status_badge = tk.Frame(title_frame, bg="#004D2C", padx=14, pady=4)
        status_badge.pack(pady=(0, 4))

        self.lbl_status = tk.Label(
            status_badge, text="🟢 CONNECTED TO ANDROID",
            font=("Segoe UI", 11, "bold"), fg="#00FF99", bg="#004D2C"
        )
        self.lbl_status.pack()

        self.connected_device_label = tk.Label(
            title_frame, text=f"📱 {self.connected_device_name}",
            font=("Segoe UI", 13, "bold"), fg="#FFFFFF", bg="#0D1B2A"
        )
        self.connected_device_label.pack(pady=(2, 2))

        lbl_connected_sub = tk.Label(
            title_frame,
            text="Local Wi-Fi link secured with AES-256-GCM + DPAPI",
            font=("Segoe UI", 8), fg="#00DD88", bg="#0D1B2A"
        )
        lbl_connected_sub.pack()

        # Activity card
        card = tk.Frame(self.connected_frame, bg="#1A2A3E", padx=12, pady=6)
        card.pack(pady=4, padx=16, fill="x")

        self.last_sync_label = tk.Label(
            card, text=f"Sync Activity: {self.last_sync_info}",
            font=("Segoe UI", 8, "bold"), fg="#00DD88", bg="#1A2A3E", anchor="w"
        )
        self.last_sync_label.pack(fill="x")

        # Paired & Connected Devices container
        lbl_dev_hdr = tk.Label(
            self.connected_frame, text="PAIRED & CONNECTED PHONES",
            font=("Segoe UI", 9, "bold"), fg="#8EA5C0", bg="#0D1B2A", anchor="w"
        )
        lbl_dev_hdr.pack(fill="x", padx=18, pady=(6, 2))

        # Container for dynamic devices list
        self.devices_list_frame = tk.Frame(self.connected_frame, bg="#0D1B2A")
        self.devices_list_frame.pack(fill="both", expand=True, padx=16, pady=2)

        self._refresh_devices_list()

        # Action Buttons
        btn_box = tk.Frame(self.connected_frame, bg="#0D1B2A")
        btn_box.pack(pady=8)

        btn_pair_new = tk.Button(
            btn_box, text="➕ Pair Another Phone", font=("Segoe UI", 9, "bold"),
            fg="#FFFFFF", bg="#0066CC", activebackground="#0055AA",
            activeforeground="#FFFFFF", bd=0, padx=10, pady=5,
            cursor="hand2", command=self._show_pair_tab
        )
        btn_pair_new.pack(side="left", padx=3)

        btn_disconnect = tk.Button(
            btn_box, text="Disconnect All", font=("Segoe UI", 9),
            fg="#FFFFFF", bg="#CC2244", activebackground="#AA1133",
            activeforeground="#FFFFFF", bd=0, padx=10, pady=5,
            cursor="hand2", command=self._on_disconnect_click
        )
        btn_disconnect.pack(side="left", padx=3)

        btn_min = tk.Button(
            btn_box, text="Minimize to Tray", font=("Segoe UI", 9),
            fg="#CCD8E8", bg="#1A2A3E", activebackground="#243750",
            activeforeground="#FFFFFF", bd=0, padx=10, pady=5,
            cursor="hand2", command=self.hide_to_tray
        )
        btn_min.pack(side="left", padx=3)

    def _refresh_devices_list(self):
        """Rebuilds the list of paired and active devices in the UI."""
        if not self.devices_list_frame or not self.root or not self.root.winfo_exists():
            return

        for child in self.devices_list_frame.winfo_children():
            child.destroy()

        paired = self.get_paired_devices_cb() if self.get_paired_devices_cb else {}
        active = self.get_active_devices_cb() if self.get_active_devices_cb else []
        active_ids = {d["id"]: d for d in active}

        # Combine all device IDs
        all_dev_ids = list(paired.keys())
        for a in active:
            if a["id"] not in all_dev_ids:
                all_dev_ids.append(a["id"])

        if not all_dev_ids:
            if self.is_connected:
                all_dev_ids = [self.connected_device_id or "default"]
                paired = {all_dev_ids[0]: {"device_id": all_dev_ids[0], "device_name": self.connected_device_name, "platform": "Android"}}
                active_ids = {all_dev_ids[0]: {"id": all_dev_ids[0], "name": self.connected_device_name}}

        if not all_dev_ids:
            lbl_empty = tk.Label(
                self.devices_list_frame,
                text="No phones paired yet.\nSwitch to 'Pair Phone' tab to scan the QR code.",
                font=("Segoe UI", 9), fg="#5D738E", bg="#0D1B2A", pady=16
            )
            lbl_empty.pack()
            return

        for dev_id in all_dev_ids:
            dev_info = paired.get(dev_id, {})
            active_info = active_ids.get(dev_id)
            is_active = active_info is not None

            d_name = dev_info.get("device_name") or (active_info.get("name") if active_info else "Android Phone")
            d_plat = dev_info.get("platform", "Android")

            row_frame = tk.Frame(self.devices_list_frame, bg="#1A2A3E", padx=10, pady=6)
            row_frame.pack(fill="x", pady=2)

            info_col = tk.Frame(row_frame, bg="#1A2A3E")
            info_col.pack(side="left", fill="x", expand=True)

            lbl_name = tk.Label(
                info_col, text=f"📱 {d_name}",
                font=("Segoe UI", 9, "bold"), fg="#FFFFFF", bg="#1A2A3E", anchor="w"
            )
            lbl_name.pack(anchor="w")

            status_text = "🟢 Active" if is_active else "⚪ Offline"
            status_color = "#00DD88" if is_active else "#7B8FA8"
            lbl_status = tk.Label(
                info_col, text=f"{d_plat} • {status_text}",
                font=("Segoe UI", 8), fg=status_color, bg="#1A2A3E", anchor="w"
            )
            lbl_status.pack(anchor="w")

            btn_col = tk.Frame(row_frame, bg="#1A2A3E")
            btn_col.pack(side="right")

            btn_ren = tk.Button(
                btn_col, text="✏️", font=("Segoe UI", 8),
                fg="#CCD8E8", bg="#243750", bd=0, padx=6, pady=2,
                cursor="hand2", command=lambda did=dev_id, dn=d_name: self._prompt_rename_device(did, dn)
            )
            btn_ren.pack(side="left", padx=2)

            if is_active and self.on_disconnect_device:
                btn_disc = tk.Button(
                    btn_col, text="Disconnect", font=("Segoe UI", 8),
                    fg="#FFAA00", bg="#243750", bd=0, padx=6, pady=2,
                    cursor="hand2", command=lambda did=dev_id: self._disconnect_device(did)
                )
                btn_disc.pack(side="left", padx=2)

            if self.on_remove_device:
                btn_rem = tk.Button(
                    btn_col, text="❌", font=("Segoe UI", 8),
                    fg="#FF6666", bg="#243750", bd=0, padx=6, pady=2,
                    cursor="hand2", command=lambda did=dev_id, dn=d_name: self._confirm_remove_device(did, dn)
                )
                btn_rem.pack(side="left", padx=2)

    def _prompt_rename_device(self, device_id: str, old_name: str):
        if not self.root or not self.root.winfo_exists():
            return
        new_name = simpledialog.askstring(
            "Rename Device",
            f"Enter new display name for '{old_name}':",
            initialvalue=old_name,
            parent=self.root
        )
        if new_name and new_name.strip():
            clean_name = new_name.strip()
            if self.on_rename_device:
                self.on_rename_device(device_id, clean_name)
            self._refresh_devices_list()

    def _confirm_remove_device(self, device_id: str, device_name: str):
        if not self.root or not self.root.winfo_exists():
            return
        confirm = messagebox.askyesno(
            "Remove Paired Device",
            f"Are you sure you want to remove '{device_name}'?\n\n"
            "This will disconnect the phone and remove it from your trusted devices. "
            "It will need to scan the pairing QR code again to reconnect.",
            parent=self.root
        )
        if confirm:
            if self.on_remove_device:
                self.on_remove_device(device_id)
            self._refresh_devices_list()

    def _disconnect_device(self, device_id: str):
        if self.on_disconnect_device:
            self.on_disconnect_device(device_id)
        self._refresh_devices_list()

    def _build_download_tab(self):
        title_frame = tk.Frame(self.download_frame, bg="#0D1B2A")
        title_frame.pack(pady=(10, 4))

        lbl_title = tk.Label(
            title_frame, text="Download Universal Clipboard APK",
            font=("Segoe UI", 14, "bold"), fg="#FFFFFF", bg="#0D1B2A"
        )
        lbl_title.pack()

        lbl_sub = tk.Label(
            title_frame,
            text="Scan with your phone's camera to install the mobile app",
            font=("Segoe UI", 9), fg="#8EA5C0", bg="#0D1B2A", wraplength=380
        )
        lbl_sub.pack(pady=(2, 0))

        # QR Code Container
        qr_frame = tk.Frame(self.download_frame, bg="#FFFFFF", padx=8, pady=8, bd=0)
        qr_frame.pack(pady=10)

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
        inst_frame.pack(pady=4, padx=20, fill="x")

        lbl_inst = tk.Label(
            inst_frame,
            text=f"Direct Local Wi-Fi Download:\n{self.download_url}\n\n"
                 f"Official GitHub Release Download:\n{self.canonical_download_url}",
            font=("Segoe UI", 8), fg="#CCD8E8", bg="#1A2A3E", justify="left"
        )
        lbl_inst.pack()

        btn_ready = tk.Button(
            self.download_frame, text="Ready to Pair? Go to Step 2 ➔",
            font=("Segoe UI", 9, "bold"), fg="#FFFFFF", bg="#008855",
            activebackground="#006644", activeforeground="#FFFFFF",
            bd=0, padx=16, pady=6, cursor="hand2",
            command=self._show_pair_tab
        )
        btn_ready.pack(pady=(8, 4))

    def _update_countdown(self):
        if not self.root or not self.root.winfo_exists():
            return
        remaining = self.session.expires_at - int(time.time())
        if remaining <= 0 or self.session.is_completed:
            if not self.session.is_completed and self.timer_label:
                try:
                    self.timer_label.config(text="⚠️ QR code expired — click Refresh Code", fg="#FF4444")
                except Exception:
                    pass
            return

        mins = remaining // 60
        secs = remaining % 60
        if self.timer_label:
            try:
                self.timer_label.config(text=f"Expires in {mins:02d}:{secs:02d}", fg="#FFAA00")
            except Exception:
                pass

        self.root.after(1000, self._update_countdown)

    def refresh_session(self):
        """Refreshes the pairing session with a new token."""
        self.session.refresh()
        if self.on_refresh_session:
            self.on_refresh_session(self.session)
        self._refresh_qr_display()
        self._update_countdown()

    def _refresh_qr_display(self):
        if self.lbl_qr_pair and self.root and self.root.winfo_exists():
            try:
                new_img = self.session.generate_qr_image(box_size=6, border=2)
                self.pair_photo_img = ImageTk.PhotoImage(new_img)
                self.lbl_qr_pair.config(image=self.pair_photo_img)
            except Exception as e:
                logger.error(f"Error refreshing QR image: {e}")

    def set_connected(self, device_name: str = "Android Phone"):
        """Switches UI to connected state, removing pairing QR."""
        self.is_connected = True
        self.connected_device_name = device_name
        self.session.is_completed = True
        active = self.get_active_devices_cb() if self.get_active_devices_cb else []
        count = len(active) if active else 1
        title_str = f"📱 {count} Phones Connected" if count > 1 else f"📱 {device_name}"
        if self.connected_device_label and self.root and self.root.winfo_exists():
            try:
                self.connected_device_label.config(text=title_str)
                self.btn_tab_connected.configure(text=f"🟢 Connected ({count})", fg="#FFFFFF")
                self._refresh_devices_list()
                self._show_connected_tab()
            except Exception as e:
                logger.error(f"Error updating connected UI: {e}")

    def set_disconnected(self):
        """Switches UI to disconnected state or updates active device count."""
        active = self.get_active_devices_cb() if self.get_active_devices_cb else []
        count = len(active)
        if count == 0:
            self.is_connected = False
            if self.root and self.root.winfo_exists():
                try:
                    self.btn_tab_connected.configure(text="⚪ Offline", fg="#7B8FA8")
                    if self.connected_device_label:
                        self.connected_device_label.config(text="📱 Paired Devices (Offline)")
                except Exception:
                    pass
        else:
            self.is_connected = True
            if self.root and self.root.winfo_exists():
                try:
                    self.btn_tab_connected.configure(text=f"🟢 Connected ({count})", fg="#FFFFFF")
                except Exception:
                    pass
        self._refresh_devices_list()

    def set_sync_info(self, info: str):
        self.last_sync_info = info
        if self.last_sync_label and self.root and self.root.winfo_exists():
            try:
                self.last_sync_label.config(text=f"Sync Activity: {info}")
            except Exception:
                pass

    def _on_disconnect_click(self):
        if self.on_disconnect:
            self.on_disconnect()
        self.set_disconnected()
        self._show_pair_tab()

    def hide_to_tray(self):
        """Hides the window to the Windows system tray."""
        if self.root and self.root.winfo_exists():
            try:
                self.root.withdraw()
            except Exception as e:
                logger.debug(f"Error hiding window: {e}")

    def unhide(self):
        """Restores and focuses the window from the tray."""
        if self.root and self.root.winfo_exists():
            try:
                self.root.deiconify()
                self.root.attributes("-topmost", True)
                self.root.after_idle(self.root.attributes, "-topmost", False)
            except Exception as e:
                logger.debug(f"Error unhiding window: {e}")

    def close(self):
        """Safely cleans up window on application shutdown."""
        self.session.is_cancelled = True
        if self.root and self.root.winfo_exists():
            try:
                self.root.destroy()
            except Exception as e:
                logger.debug(f"Error destroying window: {e}")
            self.root = None


# Alias for backward compatibility with existing tests and imports
PairingWindow = DesktopConnectionWindow
