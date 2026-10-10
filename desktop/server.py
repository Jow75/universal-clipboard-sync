"""
Universal Clipboard — Secure WebSocket Server
Implements authenticated sessions, challenge-response HMAC handshake,
rate limiting, client lifecycle tracking, and encrypted broadcasts.
"""
import os
import json
import asyncio
import logging
from aiohttp import web
from desktop.protocol import (
    PROTOCOL_VERSION,
    verify_auth_tag,
    MAX_IMAGE_SIZE_BYTES
)

logger = logging.getLogger(__name__)


class SecureWebSocketServer:
    def __init__(self, host='0.0.0.0', port=8765, master_key_bytes: bytes = None,
                 server_id: str = "desktop", server_name: str = "Windows PC",
                 on_receive=None, on_client_connected=None, on_client_disconnected=None):
        self.host = host
        self.port = port
        self.master_key_bytes = master_key_bytes
        self.server_id = server_id
        self.server_name = server_name
        self.on_receive = on_receive
        self.on_client_connected = on_client_connected
        self.on_client_disconnected = on_client_disconnected

        self.app = web.Application()
        self.app.router.add_get('/ws', self.websocket_handler)
        self.app.router.add_get('/download', self.download_apk_handler)

        # Temporary QR pairing session store
        self.active_pairing_session = None

        self.authenticated_clients = set()
        self.pending_clients = set()
        self.runner = None
        self.site = None

    def _find_apk_path(self) -> str:
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "android", "app", "build", "outputs", "apk", "debug", "app-debug.apk"),
            os.path.join(os.getcwd(), "android", "app", "build", "outputs", "apk", "debug", "app-debug.apk"),
            os.path.join(os.getcwd(), "app-debug.apk"),
        ]
        import sys
        if hasattr(sys, "executable") and sys.executable:
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            candidates.append(os.path.join(exe_dir, "app-debug.apk"))
            candidates.append(os.path.join(exe_dir, "..", "android", "app", "build", "outputs", "apk", "debug", "app-debug.apk"))
        if hasattr(sys, "_MEIPASS"):
            candidates.insert(0, os.path.join(sys._MEIPASS, "app-debug.apk"))
            candidates.insert(1, os.path.join(sys._MEIPASS, "android", "app-debug.apk"))
        for p in candidates:
            if os.path.isfile(p):
                return os.path.abspath(p)
        return ""

    async def download_apk_handler(self, request):
        """Serves mobile APK directly to phone over local Wi-Fi without internet or GitHub."""
        apk_path = self._find_apk_path()
        if apk_path and os.path.isfile(apk_path):
            logger.info(f"Serving APK directly to {request.remote} via /download")
            return web.FileResponse(
                apk_path,
                headers={
                    "Content-Type": "application/vnd.android.package-archive",
                    "Content-Disposition": 'attachment; filename="UniversalClipboard.apk"'
                }
            )
        logger.warning(f"APK download requested by {request.remote} but APK file was not found")
        return web.Response(status=404, text="APK not found on desktop host. Please rebuild or transfer APK.")

    def set_master_key(self, key_bytes: bytes):
        """Updates the master encryption key used for authentication and sync."""
        self.master_key_bytes = key_bytes

    def set_active_pairing_session(self, session_dict: dict):
        """Sets active QR pairing session info."""
        self.active_pairing_session = session_dict

    def clear_active_pairing_session(self):
        self.active_pairing_session = None

    async def websocket_handler(self, request):
        # Limit connection count to prevent resource exhaustion
        if len(self.authenticated_clients) + len(self.pending_clients) >= 8:
            logger.warning(f"Connection rejected: max clients reached ({request.remote})")
            return web.Response(status=503, text="Server busy")

        ws = web.WebSocketResponse(max_msg_size=MAX_IMAGE_SIZE_BYTES)
        await ws.prepare(request)

        self.pending_clients.add(ws)
        client_remote = request.remote
        logger.info(f"Client connected from {client_remote}, initiating challenge...")

        client_info = {"id": "unknown", "name": "unknown"}
        is_authenticated = False

        try:
            # 1. Send authentication challenge
            challenge_nonce = os.urandom(16).hex()
            challenge_msg = json.dumps({
                "v": PROTOCOL_VERSION,
                "type": "auth_challenge",
                "nonce": challenge_nonce,
                "server_id": self.server_id,
                "server_name": self.server_name
            })
            await ws.send_str(challenge_msg)

            # 2. Wait for auth response with timeout (10 seconds)
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    if not is_authenticated:
                        # Process authentication message
                        try:
                            auth_data = json.loads(msg.data)
                            msg_type = auth_data.get("type")
                            claimed_tag = auth_data.get("auth_tag")
                            client_info["id"] = auth_data.get("device_id", "unknown")
                            client_info["name"] = auth_data.get("device_name", "Android Device")

                            # Verify against master key OR active temporary QR pairing session
                            valid = False
                            is_qr_pairing = False
                            qr_token_bytes = None
                            if self.master_key_bytes and claimed_tag:
                                valid = verify_auth_tag(challenge_nonce, self.master_key_bytes, claimed_tag)

                            # If not matching master key, check active QR pairing session
                            if not valid and self.active_pairing_session:
                                session = self.active_pairing_session
                                qr_token_bytes = session.get("token_bytes")
                                if qr_token_bytes and claimed_tag:
                                    if verify_auth_tag(challenge_nonce, qr_token_bytes, claimed_tag):
                                        valid = True
                                        is_qr_pairing = True
                                        logger.info(f"Client authenticated via active QR pairing session!")

                            if valid:
                                is_authenticated = True
                                self.pending_clients.discard(ws)
                                self.authenticated_clients.add(ws)

                                ok_data = {
                                    "v": PROTOCOL_VERSION,
                                    "type": "auth_ok",
                                    "server_id": self.server_id,
                                    "server_name": self.server_name
                                }

                                # If authenticated via ephemeral QR token, provision permanent master key
                                if is_qr_pairing and qr_token_bytes and self.master_key_bytes:
                                    from desktop.crypto import CryptoManager
                                    qr_crypto = CryptoManager(qr_token_bytes)
                                    ok_data["master_key_payload"] = qr_crypto.encrypt("master_key", self.master_key_bytes.hex())
                                    logger.info("Encrypted permanent master key attached to auth_ok response.")
                                    # Invalidate temporary QR pairing session immediately (single-use)
                                    self.clear_active_pairing_session()

                                await ws.send_str(json.dumps(ok_data))
                                logger.info(f"Client authenticated: {client_info['name']} ({client_remote})")

                                if self.on_client_connected:
                                    self.on_client_connected(client_info["id"], client_info["name"])
                            else:
                                logger.warning(f"Authentication failed for client {client_remote}")
                                fail_msg = json.dumps({
                                    "v": PROTOCOL_VERSION,
                                    "type": "auth_fail",
                                    "reason": "Invalid credentials"
                                })
                                await ws.send_str(fail_msg)
                                await ws.close(code=4001, message=b"Authentication failed")
                                break
                        except Exception as e:
                            logger.error(f"Error parsing auth message: {e}")
                            await ws.close(code=4002, message=b"Malformed auth message")
                            break
                    else:
                        # Client is authenticated -> process clipboard content
                        if self.on_receive:
                            await asyncio.get_event_loop().run_in_executor(
                                None, self.on_receive, msg.data
                            )
                elif msg.type == web.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")

        except Exception as e:
            logger.error(f"WebSocket error with client {client_remote}: {e}")
        finally:
            self.pending_clients.discard(ws)
            was_auth = ws in self.authenticated_clients
            self.authenticated_clients.discard(ws)

            logger.info(f"Client disconnected: {client_remote} (was_auth={was_auth})")
            if was_auth and self.on_client_disconnected:
                self.on_client_disconnected(client_info["id"])

        return ws

    async def broadcast(self, message: str):
        """Broadcasts an encrypted payload strictly to authenticated clients."""
        if not self.authenticated_clients:
            return
        logger.info(f"Broadcasting to {len(self.authenticated_clients)} authenticated client(s).")
        tasks = [self._send_safe(ws, message) for ws in list(self.authenticated_clients)]
        if tasks:
            await asyncio.gather(*tasks)

    async def _send_safe(self, ws, message):
        try:
            await ws.send_str(message)
        except Exception as e:
            logger.error(f"Error sending to client: {e}")
            self.authenticated_clients.discard(ws)

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        logger.info(f"Secure WebSocket server active on ws://{self.host}:{self.port}/ws")

    async def stop(self):
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        logger.info("Secure WebSocket server stopped.")
