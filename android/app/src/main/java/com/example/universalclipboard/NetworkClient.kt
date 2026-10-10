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

enum class ConnectionState {
    DISCONNECTED,
    DISCOVERING,
    CONNECTING,
    AUTHENTICATING,
    CONNECTED,
    RECONNECTING,
    ERROR
}

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
    private val onTokenProvisioned: ((String) -> Unit)? = null,
    private val onStateChange: ((ConnectionState) -> Unit)? = null
) {
    private val client = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .pingInterval(20, TimeUnit.SECONDS)
        .build()

    private var webSocket: WebSocket? = null
    private var isClosed = false
    private var isAuthenticated = false
    private var state: ConnectionState = ConnectionState.DISCONNECTED
    private val handler = Handler(Looper.getMainLooper())

    // Monotonic generation number to prevent stale socket callbacks
    private var currentEpoch: Long = 0L

    private var retryAttempt = 0
    private val suppressedHashes = LinkedHashMap<String, Long>()

    // Bounded buffer for pending text if copied while reconnecting (TTL 60s)
    private var pendingText: String? = null
    private var pendingTextTime: Long = 0L

    companion object {
        private const val TAG = "NetworkClient"
        private const val UDP_DISCOVERY_PORT = 8766
        private const val UDP_DISCOVERY_MAGIC = "UNICLIP_DISCOVER"
    }

    fun isConnectedAndAuthenticated(): Boolean = webSocket != null && isAuthenticated && state == ConnectionState.CONNECTED

    fun getState(): ConnectionState = state

    private fun updateState(newState: ConnectionState) {
        state = newState
        onStateChange?.invoke(newState)
    }

    @Synchronized
    fun connect() {
        if (isClosed) return

        // Gracefully cancel any prior socket
        try {
            webSocket?.cancel()
        } catch (_: Exception) {}
        webSocket = null

        val epoch = ++currentEpoch
        val url = "ws://$ip:$port/ws"
        val request = Request.Builder().url(url).build()

        Log.d(TAG, "[epoch=$epoch] Connecting to $url ...")
        updateState(ConnectionState.CONNECTING)
        onStatusChange(MainActivity.STATUS_CONNECTING)
        isAuthenticated = false

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                if (epoch != currentEpoch || isClosed) {
                    Log.d(TAG, "[epoch=$epoch] Stale onOpen ignored (current=$currentEpoch)")
                    webSocket.cancel()
                    return
                }
                Log.d(TAG, "[epoch=$epoch] WebSocket connected, awaiting auth challenge from $ip:$port")
                updateState(ConnectionState.AUTHENTICATING)
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                if (epoch != currentEpoch || isClosed) {
                    Log.d(TAG, "[epoch=$epoch] Stale onMessage ignored (current=$currentEpoch)")
                    return
                }

                try {
                    // 1. Handshake frames
                    if (!isAuthenticated) {
                        handleHandshakeMessage(webSocket, text, epoch)
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
                    Log.e(TAG, "[epoch=$epoch] Error processing incoming frame: ${e.message}")
                }
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                if (epoch != currentEpoch || isClosed) return
                webSocket.close(1000, null)
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                if (epoch != currentEpoch || isClosed) {
                    Log.d(TAG, "[epoch=$epoch] Stale onFailure ignored (current=$currentEpoch)")
                    return
                }
                Log.e(TAG, "[epoch=$epoch] Connection failure to $ip: ${t.message}")
                isAuthenticated = false
                updateState(ConnectionState.RECONNECTING)
                onStatusChange(MainActivity.STATUS_DISCONNECTED)
                triggerUdpDiscoveryAndReconnect(epoch)
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                if (epoch != currentEpoch || isClosed) {
                    Log.d(TAG, "[epoch=$epoch] Stale onClosed ignored (current=$currentEpoch)")
                    return
                }
                Log.d(TAG, "[epoch=$epoch] Closed: code=$code, reason=$reason")
                isAuthenticated = false

                if (code == 4001) {
                    Log.w(TAG, "[epoch=$epoch] Server rejected authentication credentials.")
                    updateState(ConnectionState.ERROR)
                    onStatusChange("Pairing Invalid / Re-pair Required")
                    return
                }

                updateState(ConnectionState.RECONNECTING)
                onStatusChange(MainActivity.STATUS_DISCONNECTED)
                if (!isClosed) {
                    triggerUdpDiscoveryAndReconnect(epoch)
                }
            }
        })
    }

    private fun handleHandshakeMessage(ws: WebSocket, rawJson: String, epoch: Long) {
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
                Log.d(TAG, "[epoch=$epoch] Sent auth response challenge")

            } else if (type == Protocol.TYPE_AUTH_OK) {
                val masterKeyPayload = json.optString("master_key_payload")
                if (masterKeyPayload.isNotBlank()) {
                    try {
                        val decryptedStr = CryptoManager.decrypt(masterKeyPayload, token)
                        val keyJson = JSONObject(decryptedStr)
                        val realKey = keyJson.getString("data")
                        Log.i(TAG, "[epoch=$epoch] Successfully provisioned permanent master key via pairing handshake")
                        token = realKey
                        onTokenProvisioned?.invoke(realKey)
                    } catch (e: Exception) {
                        Log.e(TAG, "[epoch=$epoch] Failed to decrypt provisioned master key: ${e.message}")
                    }
                }
                isAuthenticated = true
                retryAttempt = 0  // Backoff reset strictly on successful auth
                updateState(ConnectionState.CONNECTED)
                onStatusChange(MainActivity.STATUS_CONNECTED)
                Log.i(TAG, "[epoch=$epoch] Successfully authenticated with desktop!")

                // Deliver pending message if queued during reconnection
                val pending = pendingText
                if (pending != null && (System.currentTimeMillis() - pendingTextTime) < 60_000) {
                    pendingText = null
                    sendText(pending)
                }

            } else if (type == Protocol.TYPE_AUTH_FAIL) {
                Log.w(TAG, "[epoch=$epoch] Server auth failed: ${json.optString("reason")}")
                updateState(ConnectionState.ERROR)
                onStatusChange("Pairing Invalid / Re-pair Required")
                ws.close(4001, "Auth Failed")
            }
        } catch (e: Exception) {
            Log.e(TAG, "[epoch=$epoch] Handshake parse error: ${e.message}")
        }
    }

    fun sendText(text: String) {
        if (text.isBlank()) return

        if (!isAuthenticated || webSocket == null || state != ConnectionState.CONNECTED) {
            // Buffer bounded text while reconnecting
            pendingText = text
            pendingTextTime = System.currentTimeMillis()
            Log.d(TAG, "Buffered text to send upon connection (${text.length} chars)")
            return
        }

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
        if (!isAuthenticated || base64.isBlank() || state != ConnectionState.CONNECTED) return
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

    fun isHashSuppressed(hash: String): Boolean {
        val time = suppressedHashes[hash] ?: return false
        return (System.currentTimeMillis() - time) < 60_000
    }

    private fun triggerUdpDiscoveryAndReconnect(epoch: Long) {
        if (isClosed || epoch != currentEpoch) return
        retryAttempt++

        // Exponential backoff: 2s, 4s, 8s, up to 30s + random jitter
        val baseDelay = Math.min(2000L * (1 shl Math.min(retryAttempt, 4)), 30_000L)
        val jitter = Random.nextLong(0, 1000)
        val delay = baseDelay + jitter

        updateState(ConnectionState.DISCOVERING)

        // Asynchronous UDP discovery to track dynamic IP changes on desktop
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
            if (!isClosed && epoch == currentEpoch) {
                connect()
            }
        }, delay)
    }

    fun close() {
        isClosed = true
        isAuthenticated = false
        updateState(ConnectionState.DISCONNECTED)
        handler.removeCallbacksAndMessages(null)
        try {
            webSocket?.close(1000, "App closed")
        } catch (_: Exception) {}
        webSocket = null
    }
}
