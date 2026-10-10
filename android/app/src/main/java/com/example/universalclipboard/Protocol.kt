package com.example.universalclipboard

import org.json.JSONObject
import java.nio.charset.StandardCharsets
import java.security.MessageDigest
import java.util.UUID
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

object Protocol {
    const val PROTOCOL_VERSION = 2
    const val TYPE_AUTH_CHALLENGE = "auth_challenge"
    const val TYPE_AUTH_RESPONSE = "auth_response"
    const val TYPE_AUTH_OK = "auth_ok"
    const val TYPE_AUTH_FAIL = "auth_fail"
    const val TYPE_PAIR_REQUEST = "pair_request"
    const val TYPE_PAIR_RESPONSE = "pair_response"

    fun normalizeText(text: String): String {
        return text.replace("\r\n", "\n").replace("\r", "\n")
    }

    fun computeContentHash(clipType: String, data: String): String {
        val digest = MessageDigest.getInstance("SHA-256")
        val bytes = if (clipType == "text") {
            normalizeText(data).toByteArray(StandardCharsets.UTF_8)
        } else {
            data.toByteArray(StandardCharsets.UTF_8)
        }
        val hashBytes = digest.digest(bytes)
        return hashBytes.joinToString("") { "%02x".format(it) }
    }

    fun computeAuthTag(nonceHex: String, keyHex: String): String {
        val keyBytes = hexStringToByteArray(keyHex)
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(keyBytes, "HmacSHA256"))
        val tagBytes = mac.doFinal(nonceHex.toByteArray(StandardCharsets.UTF_8))
        return tagBytes.joinToString("") { "%02x".format(it) }
    }

    fun buildClipboardPayload(clipType: String, data: String, sourceId: String): String {
        val hash = computeContentHash(clipType, data)
        return JSONObject().apply {
            put("v", PROTOCOL_VERSION)
            put("id", UUID.randomUUID().toString())
            put("type", clipType)
            put("data", data)
            put("source", sourceId)
            put("ts", System.currentTimeMillis() / 1000)
            put("hash", hash)
        }.toString()
    }

    fun hexStringToByteArray(s: String): ByteArray {
        val len = s.length
        val data = ByteArray(len / 2)
        var i = 0
        while (i < len) {
            data[i / 2] = ((Character.digit(s[i], 16) shl 4) + Character.digit(s[i + 1], 16)).toByte()
            i += 2
        }
        return data
    }
}
