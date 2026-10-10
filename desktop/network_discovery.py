"""
Universal Clipboard — Network Interface Discovery & UDP Beacon
Discovers valid LAN IP addresses, filters virtual interfaces,
and responds to local broadcast discovery requests from Android.
"""
import socket
import logging
import threading
import json
import ipaddress

logger = logging.getLogger(__name__)

DISCOVERY_UDP_PORT = 8766
DISCOVERY_MAGIC_REQUEST = "UNICLIP_DISCOVER"


def is_virtual_or_link_local(ip: str) -> bool:
    """Checks if an IP address belongs to loopback, link-local, or common VM subnets."""
    if not ip or ip.startswith("127.") or ip.startswith("169.254."):
        return True
    # Common VirtualBox Host-Only default
    if ip.startswith("192.168.56."):
        return True
    return False


def get_all_local_ips() -> list:
    """Returns all IPv4 addresses configured on this machine, ordered by preference."""
    candidates = []

    # Method 1: Hostname address enumeration
    try:
        _, _, ips = socket.gethostbyname_ex(socket.gethostname())
        for ip in ips:
            if not is_virtual_or_link_local(ip):
                candidates.append(ip)
    except Exception as e:
        logger.debug(f"gethostbyname_ex error: {e}")

    # Method 2: Route probe
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        probe_ip = s.getsockname()[0]
        s.close()
        if not is_virtual_or_link_local(probe_ip) and probe_ip not in candidates:
            # Place probe IP first if not virtual
            candidates.insert(0, probe_ip)
    except Exception as e:
        logger.debug(f"Route probe error: {e}")

    # Deduplicate while preserving order
    seen = set()
    result = []
    for ip in candidates:
        if ip not in seen:
            seen.add(ip)
            result.append(ip)

    if not result:
        # Fallback to localhost if no LAN adapter found
        result.append("127.0.0.1")

    return result


def get_best_local_ip() -> str:
    """Returns the primary LAN IP address to advertise to mobile clients."""
    ips = get_all_local_ips()
    # Prefer 192.168.* or 10.* over 172.* (which is frequently WSL/Docker)
    for ip in ips:
        if ip.startswith("192.168.") or ip.startswith("10."):
            return ip
    for ip in ips:
        if not ip.startswith("127."):
            return ip
    return "127.0.0.1"


class DiscoveryBeacon:
    """
    Listens for UDP broadcast packets from Android clients looking for Universal Clipboard.
    Enables automatic device discovery and seamless IP updates on DHCP changes.
    """
    def __init__(self, device_name: str, device_id: str, server_port: int = 8765, beacon_port: int = DISCOVERY_UDP_PORT):
        self.device_name = device_name
        self.device_id = device_id
        self.server_port = server_port
        self.beacon_port = beacon_port
        self.running = False
        self.thread = None
        self.sock = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()
        logger.info(f"Discovery beacon active on UDP port {self.beacon_port}")

    def stop(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        logger.info("Discovery beacon stopped.")

    def _listen_loop(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind(('', self.beacon_port))
            self.sock.settimeout(1.0)
        except Exception as e:
            logger.warning(f"Could not bind UDP discovery socket: {e}")
            return

        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = data.decode('utf-8', errors='ignore').strip()
                if message == DISCOVERY_MAGIC_REQUEST:
                    response = json.dumps({
                        "service": "uniclip",
                        "v": 2,
                        "device_name": self.device_name,
                        "device_id": self.device_id,
                        "port": self.server_port,
                        "ip": get_best_local_ip()
                    }).encode('utf-8')
                    self.sock.sendto(response, addr)
                    logger.debug(f"Replied to discovery request from {addr}")
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.debug(f"Discovery loop error: {e}")
