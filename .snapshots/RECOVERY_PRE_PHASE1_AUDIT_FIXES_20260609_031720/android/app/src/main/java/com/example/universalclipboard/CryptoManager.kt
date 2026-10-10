package com.example.universalclipboard

import android.util.Base64
import java.nio.charset.StandardCharsets
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

object CryptoManager {
    private const val ALGORITHM = "AES"
    private const val TRANSFORMATION = "AES/GCM/NoPadding"
    private const val TAG_LENGTH_BIT = 128
    private const val IV_LENGTH_BYTE = 12

    /**
     * Encrypts a JSON string using AES-256-GCM.
     * Returns a base64-encoded string: nonce (12 bytes) + ciphertext + tag.
     * Matches the Python CryptoManager.encrypt() format exactly.
     */
    fun encrypt(plaintext: String, keyHex: String): String {
        val keyBytes = hexStringToByteArray(keyHex)
        val secretKey = SecretKeySpec(keyBytes, ALGORITHM)

        val iv = ByteArray(IV_LENGTH_BYTE).also { SecureRandom().nextBytes(it) }

        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, secretKey, GCMParameterSpec(TAG_LENGTH_BIT, iv))

        val ciphertextWithTag = cipher.doFinal(plaintext.toByteArray(StandardCharsets.UTF_8))

        // Combine: nonce + ciphertext_with_tag  (same layout as Python)
        val payload = iv + ciphertextWithTag
        return Base64.encodeToString(payload, Base64.NO_WRAP)
    }

    /**
     * Decrypts a base64-encoded AES-256-GCM payload.
     * Returns the plaintext JSON string.
     */
    fun decrypt(encryptedPayload: String, keyHex: String): String {
        val keyBytes = hexStringToByteArray(keyHex)
        val secretKey = SecretKeySpec(keyBytes, ALGORITHM)

        val payload = Base64.decode(encryptedPayload, Base64.DEFAULT)

        if (payload.size < IV_LENGTH_BYTE + 16) {
            throw IllegalArgumentException("Payload too short")
        }

        val iv = payload.copyOfRange(0, IV_LENGTH_BYTE)
        val ciphertext = payload.copyOfRange(IV_LENGTH_BYTE, payload.size)

        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.DECRYPT_MODE, secretKey, GCMParameterSpec(TAG_LENGTH_BIT, iv))

        val plaintext = cipher.doFinal(ciphertext)
        return String(plaintext, StandardCharsets.UTF_8)
    }

    private fun hexStringToByteArray(s: String): ByteArray {
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
