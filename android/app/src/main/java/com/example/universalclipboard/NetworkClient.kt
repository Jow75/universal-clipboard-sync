package com.example.universalclipboard

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.util.Log
import okhttp3.*
import org.json.JSONObject
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.util.concurrent.TimeUnit
import kotlin.random.Random

class NetworkClient(
    private val context: Context,
    private var ip: String,
    private val port: Int,
    private var token: String,
    private val clientId: String,
    private val expectedServerId: String = "",
    private val onText: (String) -> Unit,
    private val onImage: (String) -> Unit,
    private val onStatusChange: (String) -> Unit = {},
    private val onIpDiscovered: ((String) -> Unit)? = null,
    private val onTokenProvisioned: ((String) -> Unit)? = null
) {
    private val client = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .pingInterval(20, TimeUnit.SECONDS)
        .build()

    private var webSocket: WebSocket? = null
    private var isClosed = false
    private var isAuthenticated = false
    private val handler = Handler(Looper.getMainLooper())

    private var retryAttempt = 0
    private val suppressedHashes = LinkedHashMap<String, Long>()

    companion object {
        private const val TAG = "NetworkClient"
        private const val UDP_DISCOVERY_PORT = 8766
        private const val UDP_DISCOVERY_MAGIC = "UNICLIP_DISCOVER"
    }

    fun isConnectedAndAuthenticated(): Boolean = webSocket != null && isAuthenticated

    fun connect() {
        if (isClosed) return
        val url = "ws://$ip:$port/ws"
        val request = Request.Builder().url(url).build()
        Log.d(TAG, "Connecting to $url ...")
        onStatusChange(MainActivity.STATUS_CONNECTING)
        isAuthenticated = false

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                Log.d(TAG, "WebSocket connected, awaiting auth challenge from $ip:$port")
                retryAttempt = 0
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    // 1. Check if unencrypted handshake frame
                    if (!isAuthenticated) {
                        handleHandshakeMessage(webSocket, text)
                        return
                    }

                    // 2. Client is authenticated: decrypt incoming clipboard payload
                    val decryptedJson = CryptoManager.decrypt(text, token)
                    val payload = JSONObject(decryptedJson)

                    val type = payload.optString("type", "")
                    val data = payload.optString("data", "")
                    val hash = payload.optString("hash", "")

                    if (hash.isNotBlank()) {
                        recordSuppressedHash(hash)
                    }

                    when (type) {
                        "text" -> onText(data)
                        "image" -> onImage(data)
                        else -> Log.w(TAG, "Unknown payload type: $type")
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Error processing incoming frame: ${e.message}")
                }
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                webSocket.close(1000, null)
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                Log.e(TAG, "Connection failure to $ip: ${t.message}")
                isAuthenticated = false
                onStatusChange(MainActivity.STATUS_DISCONNECTED)
                triggerUdpDiscoveryAndReconnect()
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                Log.d(TAG, "Closed: code=$code, reason=$reason")
                isAuthenticated = false
                onStatusChange(MainActivity.STATUS_DISCONNECTED)
                if (code == 4001) {
                    Log.w(TAG, "Server rejected authentication credentials.")
                    onStatusChange("Pairing Invalid / Re-pair Required")
                    return
                }
                if (!isClosed) {
                    triggerUdpDiscoveryAndReconnect()
                }
            }
        })
    }

    private fun handleHandshakeMessage(ws: WebSocket, rawJson: String) {
        try {
            val json = JSONObject(rawJson)
            val type = json.optString("type")
            if (type == Protocol.TYPE_AUTH_CHALLENGE) {
                val nonce = json.getString("nonce")
                val authTag = Protocol.computeAuthTag(nonce, token)
                val deviceName = "${android.os.Build.MANUFACTURER} ${android.os.Build.MODEL}"

                val resp = JSONObject().apply {
                    put("v", Protocol.PROTOCOL_VERSION)
                    put("type", Protocol.TYPE_AUTH_RESPONSE)
                    put("device_id", clientId)
                    put("device_name", deviceName)
                    put("auth_tag", authTag)
                }.toString()

                ws.send(resp)
                Log.d(TAG, "Sent auth response challenge response")
            } else if (type == Protocol.TYPE_AUTH_OK) {
                val masterKeyPayload = json.optString("master_key_payload")
                if (masterKeyPayload.isNotBlank()) {
                    try {
                        val decryptedStr = CryptoManager.decrypt(masterKeyPayload, token)
                        val keyJson = JSONObject(decryptedStr)
                        val realKey = keyJson.getString("data")
                        Log.i(TAG, "Successfully provisioned permanent master key via pairing handshake")
                        token = realKey
                        onTokenProvisioned?.invoke(realKey)
                    } catch (e: Exception) {
                        Log.e(TAG, "Failed to decrypt provisioned master key: ${e.message}")
                    }
                }
                isAuthenticated = true
                onStatusChange(MainActivity.STATUS_CONNECTED)
                Log.i(TAG, "Successfully authenticated with desktop!")
            } else if (type == Protocol.TYPE_AUTH_FAIL) {
                Log.w(TAG, "Server auth failed: ${json.optString("reason")}")
                onStatusChange("Pairing Invalid / Re-pair Required")
                ws.close(4001, "Auth Failed")
            }
        } catch (e: Exception) {
            Log.e(TAG, "Handshake parse error: ${e.message}")
        }
    }

    fun sendText(text: String) {
        if (!isAuthenticated || text.isBlank()) return
        try {
            val hash = Protocol.computeContentHash("text", text)
            if (isHashSuppressed(hash)) return
            recordSuppressedHash(hash)

            val jsonPayload = Protocol.buildClipboardPayload("text", text, clientId)
            val encrypted = CryptoManager.encrypt(jsonPayload, token)
            webSocket?.send(encrypted)
            Log.d(TAG, "Sent text payload (${text.length} chars) to PC")
        } catch (e: Exception) {
            Log.e(TAG, "Error sending text: ${e.message}")
        }
    }

    fun sendImage(base64: String) {
        if (!isAuthenticated || base64.isBlank()) return
        try {
            val hash = Protocol.computeContentHash("image", base64)
            if (isHashSuppressed(hash)) return
            recordSuppressedHash(hash)

            val jsonPayload = Protocol.buildClipboardPayload("image", base64, clientId)
            val encrypted = CryptoManager.encrypt(jsonPayload, token)
            webSocket?.send(encrypted)
            Log.d(TAG, "Sent image payload (${base64.length} chars b64) to PC")
        } catch (e: Exception) {
            Log.e(TAG, "Error sending image: ${e.message}")
        }
    }

    private fun recordSuppressedHash(hash: String) {
        val now = System.currentTimeMillis()
        suppressedHashes[hash] = now
        val iterator = suppressedHashes.entries.iterator()
        while (iterator.hasNext()) {
            val entry = iterator.next()
            if (now - entry.value > 60_000) {
                iterator.remove()
            }
        }
    }

    private fun isHashSuppressed(hash: String): Boolean {
        val time = suppressedHashes[hash] ?: return false
        return (System.currentTimeMillis() - time) < 60_000
    }

    private fun triggerUdpDiscoveryAndReconnect() {
        if (isClosed) return
        retryAttempt++
        // Calculate backoff: 2s, 4s, 8s, up to 25s + jitter
        val baseDelay = Math.min(2000L * (1 shl Math.min(retryAttempt, 4)), 25_000L)
        val jitter = Random.nextLong(0, 1000)
        val delay = baseDelay + jitter

        // In parallel, attempt UDP discovery to see if PC changed IP
        Thread {
            try {
                val socket = DatagramSocket().apply {
                    broadcast = true
                    soTimeout = 2000
                }
                val reqData = UDP_DISCOVERY_MAGIC.toByteArray()
                val packet = DatagramPacket(
                    reqData, reqData.size,
                    InetAddress.getByName("255.255.255.255"), UDP_DISCOVERY_PORT
                )
                socket.send(packet)

                val buf = ByteArray(1024)
                val respPacket = DatagramPacket(buf, buf.size)
                socket.receive(respPacket)
                val respStr = String(respPacket.data, 0, respPacket.length)
                val json = JSONObject(respStr)
                val service = json.optString("service")
                val discoveredIp = json.optString("ip")
                val discoveredDeviceId = json.optString("device_id")

                if (service == "uniclip" && (expectedServerId.isBlank() || discoveredDeviceId == expectedServerId)) {
                    if (discoveredIp.isNotBlank() && discoveredIp != ip) {
                        Log.i(TAG, "UDP Discovery found verified PC IP: $discoveredIp (was $ip)")
                        ip = discoveredIp
                        onIpDiscovered?.invoke(discoveredIp)
                    }
                }
                socket.close()
            } catch (e: Exception) {
                Log.d(TAG, "UDP discovery did not find beacon: ${e.message}")
            }
        }.start()

        handler.postDelayed({
            if (!isClosed) {
                connect()
            }
        }, delay)
    }

    fun close() {
        isClosed = true
        isAuthenticated = false
        handler.removeCallbacksAndMessages(null)
        webSocket?.close(1000, "App closed")
        webSocket = null
    }
}
