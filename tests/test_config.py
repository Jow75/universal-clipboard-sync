import os
import sys
import unittest
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from desktop import config


class TestConfigPersistence(unittest.TestCase):
    def setUp(self):
        # Override config dir to temporary test path
        self.original_get_dir = config.get_config_dir
        self.test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "tmp_config_test"))
        config.get_config_dir = lambda: self.test_dir
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def tearDown(self):
        config.get_config_dir = self.original_get_dir
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_key_persistence_across_restarts(self):
        # 1. First run: generates config
        cfg1 = config.get_or_create_config()
        key1 = cfg1["master_key_hex"]
        dev_id1 = cfg1["device_id"]
        self.assertEqual(len(key1), 64)
        self.assertTrue(bool(dev_id1))

        # 2. Simulated restart: loads existing config
        cfg2 = config.get_or_create_config()
        key2 = cfg2["master_key_hex"]
        dev_id2 = cfg2["device_id"]

        # MUST BE IDENTICAL!
        self.assertEqual(key1, key2)
        self.assertEqual(dev_id1, dev_id2)

    def test_regenerate_key(self):
        cfg1 = config.get_or_create_config()
        old_key = cfg1["master_key_hex"]
        new_key = config.regenerate_master_key()
        self.assertNotEqual(old_key, new_key)

        # After reload, new key is returned
        cfg2 = config.get_or_create_config()
        self.assertEqual(cfg2["master_key_hex"], new_key)


if __name__ == "__main__":
    unittest.main()
