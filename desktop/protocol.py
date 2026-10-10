"""
Universal Clipboard — Unified Message Protocol & Handshake
Defines message schemas, HMAC-SHA256 challenge-response authentication,
content normalization, and SHA-256 deduplication.
"""
import hmac
import hashlib
import json
import time
import uuid

PROTOCOL_VERSION = 2
MAX_TEXT_SIZE_BYTES = 5 * 1024 * 1024     # 5 MB max text
MAX_IMAGE_SIZE_BYTES = 25 * 1024 * 1024   # 25 MB max image base64


def normalize_text(text: str) -> str:
    """Normalizes CRLF to LF to ensure consistent cross-platform hashes."""
    if not text:
        return ""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def compute_content_hash(clip_type: str, data: str) -> str:
    """
    Computes a canonical SHA-256 hex digest for clipboard content.
    Identical across Python and Kotlin implementations.
    """
    if clip_type == 'text':
        normalized = normalize_text(data)
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    else:
        # For image (base64 string)
        return hashlib.sha256(data.encode('utf-8')).hexdigest()


def compute_auth_tag(nonce_hex: str, key_bytes: bytes) -> str:
    """Computes HMAC-SHA256 authentication response for a challenge nonce."""
    return hmac.new(key_bytes, nonce_hex.encode('utf-8'), hashlib.sha256).hexdigest()


def verify_auth_tag(nonce_hex: str, key_bytes: bytes, claimed_tag: str) -> bool:
    """Constant-time verification of HMAC-SHA256 auth response."""
    expected_tag = compute_auth_tag(nonce_hex, key_bytes)
    return hmac.compare_digest(expected_tag, claimed_tag)


def build_clipboard_payload(clip_type: str, data: str, source_id: str) -> dict:
    """Builds a versioned clipboard message dictionary."""
    content_hash = compute_content_hash(clip_type, data)
    return {
        "v": PROTOCOL_VERSION,
        "id": str(uuid.uuid4()),
        "type": clip_type,
        "data": data,
        "source": source_id,
        "ts": int(time.time()),
        "hash": content_hash
    }


def parse_clipboard_payload(payload_dict: dict) -> tuple:
    """
    Validates and extracts (clip_type, data, content_hash) from dictionary.
    Raises ValueError on invalid/malformed payloads.
    """
    if not isinstance(payload_dict, dict):
        raise ValueError("Payload must be a dictionary")

    clip_type = payload_dict.get("type")
    data = payload_dict.get("data")
    if clip_type not in ("text", "image"):
        raise ValueError(f"Invalid clip type: {clip_type}")

    if not isinstance(data, str):
        raise ValueError("Data must be string")

    if clip_type == "text" and len(data.encode('utf-8')) > MAX_TEXT_SIZE_BYTES:
        raise ValueError("Text payload exceeds maximum allowed size")

    if clip_type == "image" and len(data) > MAX_IMAGE_SIZE_BYTES:
        raise ValueError("Image payload exceeds maximum allowed size")

    content_hash = payload_dict.get("hash") or compute_content_hash(clip_type, data)
    return clip_type, data, content_hash
