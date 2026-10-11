"""
Universal Clipboard — Desktop Configuration & Secure Credential Store
Stores device identity, preferences, and DPAPI-encrypted master pairing secrets.
"""
import os
import json
import uuid
import socket
import logging
import base64

logger = logging.getLogger(__name__)

# DPAPI integration for Windows
try:
    import win32crypt
    DPAPI_AVAILABLE = True
except ImportError:
    DPAPI_AVAILABLE = False


def get_config_dir() -> str:
    """Returns directory path for storing application configuration."""
    appdata = os.environ.get('APPDATA')
    if appdata:
        path = os.path.join(appdata, "UniversalClipboard")
    else:
        path = os.path.join(os.path.expanduser("~"), ".universal_clipboard")
    os.makedirs(path, exist_ok=True)
    return path


def get_config_path() -> str:
    return os.path.join(get_config_dir(), "config.json")


def _protect_secret(secret_str: str) -> str:
    """Encrypts secret with Windows DPAPI and returns base64 string."""
    if not DPAPI_AVAILABLE or not secret_str:
        return secret_str
    try:
        raw_bytes = secret_str.encode('utf-8')
        protected = win32crypt.CryptProtectData(raw_bytes, "UniversalClipboardKey", None, None, None, 0)
        return "DPAPI:" + base64.b64encode(protected).decode('utf-8')
    except Exception as e:
        logger.warning(f"DPAPI encryption failed, storing fallback: {e}")
        return secret_str


def _unprotect_secret(stored_str: str) -> str:
    """Decrypts DPAPI-protected secret string."""
    if not stored_str:
        return ""
    if stored_str.startswith("DPAPI:") and DPAPI_AVAILABLE:
        try:
            b64_data = stored_str[len("DPAPI:"):]
            raw_bytes = base64.b64decode(b64_data)
            _, decrypted = win32crypt.CryptUnprotectData(raw_bytes, None, None, None, 0)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"DPAPI decryption failed: {e}")
            return ""
    return stored_str


def load_config() -> dict:
    """Loads configuration dictionary from disk."""
    path = get_config_path()
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Decrypt master key if protected
            if "master_key_protected" in data:
                data["master_key_hex"] = _unprotect_secret(data["master_key_protected"])
            return data
    except Exception as e:
        logger.error(f"Failed to read config file: {e}")
        return {}


def save_config(config: dict) -> None:
    """Saves configuration atomically to disk."""
    path = get_config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = path + ".tmp"
    try:
        data_to_write = dict(config)
        # Protect master key using DPAPI
        if "master_key_hex" in data_to_write and data_to_write["master_key_hex"]:
            protected = _protect_secret(data_to_write["master_key_hex"])
            data_to_write["master_key_protected"] = protected
            # Do not write plaintext key to disk
            del data_to_write["master_key_hex"]

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data_to_write, f, indent=2)
        os.replace(temp_path, path)
    except Exception as e:
        logger.error(f"Failed to save config file: {e}")
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


def get_or_create_config() -> dict:
    """
    Returns application configuration.
    Guarantees consistent device_id and persistent master_key_hex across restarts.
    """
    config = load_config()
    changed = False

    if not config.get("device_id"):
        config["device_id"] = str(uuid.uuid4())
        changed = True

    if not config.get("device_name"):
        try:
            config["device_name"] = socket.gethostname()
        except Exception:
            config["device_name"] = "Windows PC"
        changed = True

    # Reuse existing master key; only generate if completely absent or corrupted
    key = config.get("master_key_hex")
    if not key or len(key) != 64:
        config["master_key_hex"] = os.urandom(32).hex()
        changed = True

    if "port" not in config:
        config["port"] = 8765
        changed = True

    if "auto_sync" not in config:
        config["auto_sync"] = True
        changed = True

    if "hotkey_mode" not in config:
        config["hotkey_mode"] = False
        changed = True

    if "paired_devices" not in config:
        config["paired_devices"] = {}
        changed = True

    if changed:
        save_config(config)

    return config


def regenerate_master_key() -> str:
    """
    Explicit user-initiated key reset.
    Generates new key, revokes existing pairings, and saves config.
    """
    config = load_config()
    new_key = os.urandom(32).hex()
    config["master_key_hex"] = new_key
    config["paired_devices"] = {}
    save_config(config)
    logger.info("Master pairing key regenerated. All paired devices revoked.")
    return new_key


def get_paired_devices() -> dict:
    """Returns dictionary of paired devices: {device_id: device_info}."""
    cfg = load_config()
    return cfg.get("paired_devices", {})


def add_or_update_paired_device(device_id: str, device_name: str, platform: str = "Android") -> dict:
    """
    Persistently stores or updates a paired device.
    Reuses existing device identity without creating duplicate records.
    """
    import time
    config = load_config()
    if "paired_devices" not in config:
        config["paired_devices"] = {}

    now = time.time()
    existing = config["paired_devices"].get(device_id, {})
    paired_at = existing.get("paired_at", now)

    config["paired_devices"][device_id] = {
        "device_id": device_id,
        "device_name": device_name,
        "platform": platform,
        "paired_at": paired_at,
        "last_seen": now,
        "status": "paired"
    }
    save_config(config)
    logger.info(f"Saved paired device {device_name} ({device_id}) to persistent config.")
    return config["paired_devices"][device_id]


def remove_paired_device(device_id: str) -> bool:
    """Removes a specific device from paired_devices without wiping other phones."""
    config = load_config()
    if "paired_devices" in config and device_id in config["paired_devices"]:
        del config["paired_devices"][device_id]
        save_config(config)
        logger.info(f"Removed paired device {device_id} from persistent config.")
        return True
    return False


def rename_paired_device(device_id: str, new_name: str) -> bool:
    """Renames an existing paired device."""
    config = load_config()
    if "paired_devices" in config and device_id in config["paired_devices"]:
        config["paired_devices"][device_id]["device_name"] = new_name
        save_config(config)
        logger.info(f"Renamed paired device {device_id} to '{new_name}'.")
        return True
    return False


def update_device_last_seen(device_id: str) -> bool:
    """Updates last_seen timestamp for a device."""
    import time
    config = load_config()
    if "paired_devices" in config and device_id in config["paired_devices"]:
        config["paired_devices"][device_id]["last_seen"] = time.time()
        save_config(config)
        return True
    return False
