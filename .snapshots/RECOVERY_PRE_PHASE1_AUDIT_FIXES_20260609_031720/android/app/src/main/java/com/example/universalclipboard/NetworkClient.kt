package com.example.universalclipboard

import android.content.ClipboardManager
import android.content.Context
import android.util.Log
import android.os.Handler
import android.os.Looper
import okhttp3.*
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class NetworkClient(
    private val context: Context,
    private val ip: String,
    private val port: Int,
    private val token: String,
    private val onText: (String) -> Unit,
    private val onImage: (String) -> Unit,
    private val onStatusChange: (String) -> Unit = {}
) {
    private val client = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .pingInterval(20, TimeUnit.SECONDS)
        .build()

    private var webSocket: WebSocket? = null
    private var isClosed = false
    private val handler = Handler(Looper.getMainLooper())
    private val reconnectDelay = 5000L

    // Tracks last clipboard hash to avoid echo-back
    private var lastSentHash: String = ""

    fun connect() {
        if (isClosed) return
        val request = Request.Builder().url("ws://$ip:$port/ws").build()
        Log.d("NetworkClient", "Connecting to ws://$ip:$port/ws ...")
        onStatusChange(MainActivity.STATUS_CONNECTING)

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                Log.d("NetworkClient", "Connected to $ip:$port")
                onStatusChange(MainActivity.STATUS_CONNECTED)
                startClipboardMonitor()
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                Log.d("NetworkClient", "Message received (len=${text.length})")
                try {
                    val decryptedJson = CryptoManager.decrypt(text, token)
                    val payload = JSONObject(decryptedJson)
                    val type = payload.getString("type")
                    val data = payload.getString("data")

                    // Track what was received so we don't echo it back
                    val hash = data.hashCode().toString()
                    lastSentHash = hash

                    when (type) {
                        "text"  -> onText(data)
                        "image" -> onImage(data)
                        else    -> Log.w("NetworkClient", "Unknown type: $type")
                    }
                } catch (e: Exception) {
                    Log.e("NetworkClient", "Error processing message: ${e.message}")
                }
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                webSocket.close(1000, null)
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                Log.e("NetworkClient", "Failure: ${t.message}")
                onStatusChange(MainActivity.STATUS_DISCONNECTED)
                scheduleReconnect()
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                Log.d("NetworkClient", "Closed: $code / $reason")
                onStatusChange(MainActivity.STATUS_DISCONNECTED)
                if (code != 1000) scheduleReconnect()
            }
        })
    }

    // ── Phone→Laptop: send current clipboard to the laptop ──────────────────
    fun sendClipboardToLaptop() {
        try {
            val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = clipboard.primaryClip ?: return
            val item = clip.getItemAt(0) ?: return
            val text = item.text?.toString() ?: return
            if (text.isBlank()) return
            sendText(text)
        } catch (e: Exception) {
            Log.e("NetworkClient", "Error reading clipboard: ${e.message}")
        }
    }

    /**
     * Called from ClipboardService when MainActivity reads the clipboard in the
     * foreground (bypassing the Android 10+ background clipboard block).
     */
    fun sendText(text: String) {
        try {
            if (text.isBlank()) return
            val hash = text.hashCode().toString()
            if (hash == lastSentHash) return  // don't echo back
            lastSentHash = hash

            val jsonPayload = org.json.JSONObject().apply {
                put("type", "text")
                put("data", text)
            }.toString()
            val encrypted = CryptoManager.encrypt(jsonPayload, token)
            webSocket?.send(encrypted)
            Log.d("NetworkClient", "Phone->Laptop: sent text (${text.length} chars)")
        } catch (e: Exception) {
            Log.e("NetworkClient", "Error sending text: ${e.message}")
        }
    }

    /**
     * Sends a base64-encoded PNG image from phone to the laptop.
     */
    fun sendImage(base64: String) {
        try {
            if (base64.isBlank()) return
            val hash = base64.hashCode().toString()
            if (hash == lastSentHash) return
            lastSentHash = hash

            val jsonPayload = org.json.JSONObject().apply {
                put("type", "image")
                put("data", base64)
            }.toString()
            val encrypted = CryptoManager.encrypt(jsonPayload, token)
            webSocket?.send(encrypted)
            Log.d("NetworkClient", "Phone->Laptop: sent image (${base64.length} chars b64)")
        } catch (e: Exception) {
            Log.e("NetworkClient", "Error sending image: ${e.message}")
        }
    }



    // ── Auto-monitor clipboard on Android ───────────────────────────────────
    private var clipboardMonitor: ClipboardManager.OnPrimaryClipChangedListener? = null

    private fun startClipboardMonitor() {
        handler.post {
            try {
                val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                clipboardMonitor = ClipboardManager.OnPrimaryClipChangedListener {
                    handler.postDelayed({ sendClipboardToLaptop() }, 300)
                }
                clipboard.addPrimaryClipChangedListener(clipboardMonitor!!)
                Log.d("NetworkClient", "Clipboard monitor started")
            } catch (e: Exception) {
                Log.e("NetworkClient", "Could not start clipboard monitor: ${e.message}")
            }
        }
    }

    private fun stopClipboardMonitor() {
        handler.post {
            try {
                clipboardMonitor?.let {
                    val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                    clipboard.removePrimaryClipChangedListener(it)
                    clipboardMonitor = null
                }
            } catch (e: Exception) {
                Log.e("NetworkClient", "Error stopping clipboard monitor: ${e.message}")
            }
        }
    }

    private fun scheduleReconnect() {
        if (isClosed) return
        handler.removeCallbacksAndMessages(null)
        handler.postDelayed({
            if (!isClosed) {
                Log.d("NetworkClient", "Reconnecting...")
                connect()
            }
        }, reconnectDelay)
    }

    fun close() {
        isClosed = true
        stopClipboardMonitor()
        handler.removeCallbacksAndMessages(null)
        webSocket?.close(1000, "Goodbye")
    }
}
