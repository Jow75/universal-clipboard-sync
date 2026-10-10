package com.example.universalclipboard

import android.content.Context
import android.content.SharedPreferences
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import java.util.UUID
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class SecureStorage(context: Context) {

    private val prefs: SharedPreferences =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    companion object {
        private const val PREFS_NAME = "universal_clipboard_secure_prefs"
        private const val ANDROID_KEYSTORE = "AndroidKeyStore"
        private const val KEY_ALIAS = "UniversalClipboardKeyAlias"
        private const val GCM_TAG_LENGTH = 128
        private const val IV_LENGTH = 12

        private const val KEY_IS_PAIRED = "is_paired"
        private const val KEY_ENC_TOKEN = "enc_token"
        private const val KEY_LAST_IP = "last_ip"
        private const val KEY_PORT = "port"
        private const val KEY_DEVICE_NAME = "device_name"
        private const val KEY_DEVICE_ID = "device_id"
        private const val KEY_CLIENT_ID = "client_id"
    }

    init {
        ensureKeyStoreKey()
    }

    private fun ensureKeyStoreKey() {
        try {
            val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
            if (!keyStore.containsAlias(KEY_ALIAS)) {
                val keyGen = KeyGenerator.getInstance(
                    KeyProperties.KEY_ALGORITHM_AES, ANDROID_KEYSTORE
                )
                val spec = KeyGenParameterSpec.Builder(
                    KEY_ALIAS,
                    KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
                )
                    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                    .setKeySize(256)
                    .build()
                keyGen.init(spec)
                keyGen.generateKey()
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun getSecretKey(): SecretKey? {
        val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
        return keyStore.getKey(KEY_ALIAS, null) as? SecretKey
    }

    private fun encryptString(plaintext: String): String {
        return try {
            val secretKey = getSecretKey() ?: return plaintext
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.ENCRYPT_MODE, secretKey)
            val iv = cipher.iv
            val ciphertext = cipher.doFinal(plaintext.toByteArray(Charsets.UTF_8))
            val combined = iv + ciphertext
            Base64.encodeToString(combined, Base64.NO_WRAP)
        } catch (e: Exception) {
            e.printStackTrace()
            plaintext
        }
    }

    private fun decryptString(encoded: String): String {
        return try {
            val secretKey = getSecretKey() ?: return encoded
            val raw = Base64.decode(encoded, Base64.NO_WRAP)
            if (raw.size < IV_LENGTH + 16) return encoded
            val iv = raw.copyOfRange(0, IV_LENGTH)
            val ciphertext = raw.copyOfRange(IV_LENGTH, raw.size)
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.DECRYPT_MODE, secretKey, GCMParameterSpec(GCM_TAG_LENGTH, iv))
            val plainBytes = cipher.doFinal(ciphertext)
            String(plainBytes, Charsets.UTF_8)
        } catch (e: Exception) {
            e.printStackTrace()
            encoded
        }
    }

    fun savePairing(ip: String, port: Int, tokenHex: String, serverName: String, serverId: String) {
        val encToken = encryptString(tokenHex)
        prefs.edit()
            .putBoolean(KEY_IS_PAIRED, true)
            .putString(KEY_ENC_TOKEN, encToken)
            .putString(KEY_LAST_IP, ip)
            .putInt(KEY_PORT, port)
            .putString(KEY_DEVICE_NAME, serverName)
            .putString(KEY_DEVICE_ID, serverId)
            .apply()
    }

    fun isPaired(): Boolean = prefs.getBoolean(KEY_IS_PAIRED, false)

    fun getPairedToken(): String? {
        val enc = prefs.getString(KEY_ENC_TOKEN, null) ?: return null
        return decryptString(enc)
    }

    fun getPairedIp(): String = prefs.getString(KEY_LAST_IP, "") ?: ""

    fun updatePairedIp(newIp: String) {
        prefs.edit().putString(KEY_LAST_IP, newIp).apply()
    }

    fun updateToken(newTokenHex: String) {
        val encToken = encryptString(newTokenHex)
        prefs.edit().putString(KEY_ENC_TOKEN, encToken).apply()
    }

    fun getPairedPort(): Int = prefs.getInt(KEY_PORT, 8765)

    fun getPairedDeviceName(): String = prefs.getString(KEY_DEVICE_NAME, "Windows PC") ?: "Windows PC"

    fun getPairedDeviceId(): String = prefs.getString(KEY_DEVICE_ID, "") ?: ""

    fun clearPairing() {
        prefs.edit().clear().putBoolean(KEY_IS_PAIRED, false).apply()
    }

    fun getOrCreateClientId(): String {
        var id = prefs.getString(KEY_CLIENT_ID, null)
        if (id.isNullOrBlank()) {
            id = UUID.randomUUID().toString()
            prefs.edit().putString(KEY_CLIENT_ID, id).apply()
        }
        return id
    }
}
