import socket
import json
import time
import unittest

from desktop import network_discovery


class TestNetworkDiscovery(unittest.TestCase):
    def test_filter_virtual_ips(self):
        self.assertTrue(network_discovery.is_virtual_or_link_local("127.0.0.1"))
        self.assertTrue(network_discovery.is_virtual_or_link_local("169.254.10.20"))
        self.assertTrue(network_discovery.is_virtual_or_link_local("192.168.56.1"))
        self.assertFalse(network_discovery.is_virtual_or_link_local("192.168.1.100"))
        self.assertFalse(network_discovery.is_virtual_or_link_local("10.0.0.5"))

    def test_get_best_local_ip(self):
        ip = network_discovery.get_best_local_ip()
        self.assertIsInstance(ip, str)
        self.assertNotEqual(ip, "")

    def test_discovery_beacon_roundtrip(self):
        test_port = 18766
        beacon = network_discovery.DiscoveryBeacon("TestPC", "test-device-id-123", server_port=8765, beacon_port=test_port)
        beacon.start()
        time.sleep(0.2)

        # Send discover request via UDP client
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_sock.settimeout(2.0)
        try:
            client_sock.sendto(
                network_discovery.DISCOVERY_MAGIC_REQUEST.encode('utf-8'),
                ("127.0.0.1", test_port)
            )
            data, _ = client_sock.recvfrom(1024)
            parsed = json.loads(data.decode('utf-8'))
            self.assertEqual(parsed.get("service"), "uniclip")
            self.assertEqual(parsed.get("device_name"), "TestPC")
            self.assertEqual(parsed.get("device_id"), "test-device-id-123")
            self.assertEqual(parsed.get("port"), 8765)
        finally:
            client_sock.close()
            beacon.stop()


if __name__ == "__main__":
    unittest.main()
