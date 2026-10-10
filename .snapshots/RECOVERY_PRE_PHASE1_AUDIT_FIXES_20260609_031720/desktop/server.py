import asyncio
import base64
import json
import logging
from aiohttp import web

class WebSocketServer:
    def __init__(self, host='0.0.0.0', port=8765, on_receive=None):
        """
        on_receive: callback(clip_type: str, data: str) called when Android sends
                    clipboard content to the desktop.
        """
        self.host = host
        self.port = port
        self.on_receive = on_receive
        self.app = web.Application()          # WebSocket limit set per-handler below
        self.app.router.add_get('/ws', self.websocket_handler)
        self.clients = set()
        self.runner = None
        self.site = None
        self.logger = logging.getLogger(__name__)

    async def websocket_handler(self, request):
        ws = web.WebSocketResponse(max_msg_size=20 * 1024 * 1024)
        await ws.prepare(request)

        self.clients.add(ws)
        self.logger.info(f"Client connected: {request.remote}")

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    # Android is sending clipboard content to us
                    if self.on_receive:
                        await asyncio.get_event_loop().run_in_executor(
                            None, self.on_receive, msg.data
                        )
                elif msg.type == web.WSMsgType.ERROR:
                    self.logger.error(f"WebSocket error: {ws.exception()}")
        except Exception as e:
            self.logger.error(f"WebSocket handler error: {e}")
        finally:
            self.clients.discard(ws)
            self.logger.info(f"Client disconnected: {request.remote}")

        return ws

    async def broadcast(self, message: str):
        """Broadcasts an encrypted payload to all connected Android clients."""
        if not self.clients:
            return
        self.logger.info(f"Broadcasting to {len(self.clients)} client(s).")
        tasks = [self._send_safe(ws, message) for ws in list(self.clients)]
        if tasks:
            await asyncio.gather(*tasks)

    async def _send_safe(self, ws, message):
        try:
            await ws.send_str(message)
        except Exception as e:
            self.logger.error(f"Error sending to client: {e}")
            self.clients.discard(ws)

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        self.logger.info(f"WebSocket server started on ws://{self.host}:{self.port}/ws")

    async def stop(self):
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        self.logger.info("WebSocket server stopped.")
