package com.example.universalclipboard

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.localbroadcastmanager.content.LocalBroadcastManager
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class ClipboardService : Service() {
    internal var networkClient: NetworkClient? = null
    private lateinit var clipboardHandler: ClipboardHandler
    private lateinit var secureStorage: SecureStorage
    private var clipboardManager: ClipboardManager? = null
    private var lastObservedClipHash: String = ""
    private val CHANNEL_ID = "ClipboardServiceChannel"

    private val clipChangedListener = ClipboardManager.OnPrimaryClipChangedListener {
        readAndSendActiveClipboard(isAutoSync = true)
    }

    companion object {
        const val ACTION_SEND_TEXT     = "com.example.universalclipboard.SEND_TEXT"
        const val ACTION_TRIGGER_SEND  = "com.example.universalclipboard.TRIGGER_SEND"
        const val EXTRA_TEXT           = "text"

        var instance: ClipboardService? = null
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
        clipboardHandler = ClipboardHandler(this)
        secureStorage = SecureStorage(this)
        createNotificationChannel()

        clipboardManager = getSystemService(Context.CLIPBOARD_SERVICE) as? ClipboardManager
        try {
            clipboardManager?.addPrimaryClipChangedListener(clipChangedListener)
        } catch (e: Exception) {
            Log.w("ClipboardService", "Could not register clipChangedListener: ${e.message}")
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        // ── 1. Action: Direct text send ──
        if (intent?.action == ACTION_SEND_TEXT) {
            val text = intent.getStringExtra(EXTRA_TEXT)
            if (!text.isNullOrBlank()) {
                networkClient?.sendText(text)
                broadcastSyncEvent("Sent text to PC (${text.length} chars)")
            }
            return START_STICKY
        }

        // ── 2. Action: Trigger send from Notification Button or Tile ──
        if (intent?.action == ACTION_TRIGGER_SEND) {
            readAndSendActiveClipboard()
            return START_STICKY
        }

        // ── 3. Normal Start / Connect ──
        var ip = intent?.getStringExtra("IP")
        var token = intent?.getStringExtra("TOKEN")

        if (ip.isNullOrBlank() || token.isNullOrBlank()) {
            // Restore from secure storage
            ip = secureStorage.getPairedIp()
            token = secureStorage.getPairedToken()
        }

        if (!ip.isNullOrBlank() && !token.isNullOrBlank()) {
            startForeground(1, buildNotification("Connecting…"))
            broadcastStatus(MainActivity.STATUS_CONNECTING)

            networkClient?.close()
            val clientId = secureStorage.getOrCreateClientId()
            val port = secureStorage.getPairedPort()

            val expectedServerId = secureStorage.getPairedDeviceId()

            networkClient = NetworkClient(
                context = this,
                ip = ip,
                port = port,
                token = token,
                clientId = clientId,
                expectedServerId = expectedServerId,
                onText = { text ->
                    clipboardHandler.copyToClipboard(text)
                    broadcastSyncEvent("Received text from PC")
                },
                onImage = { b64 ->
                    clipboardHandler.copyImageToClipboard(b64)
                    broadcastSyncEvent("Received image from PC")
                },
                onStatusChange = { status ->
                    broadcastStatus(status)
                },
                onIpDiscovered = { newIp ->
                    secureStorage.updatePairedIp(newIp)
                },
                onTokenProvisioned = { newPermanentKey ->
                    secureStorage.updateToken(newPermanentKey)
                    Log.i("ClipboardService", "Permanent master key secured in Android Keystore")
                }
            )
            networkClient?.connect()
            Log.d("ClipboardService", "Connected client initiated for $ip:$port")
        }

        return START_STICKY
    }

    fun readAndSendActiveClipboard(isAutoSync: Boolean = false) {
        try {
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = clipboard.primaryClip
            if (clip != null && clip.itemCount > 0) {
                val item = clip.getItemAt(0)
                val text = item.coerceToText(this)?.toString()
                if (!text.isNullOrBlank()) {
                    val hash = Protocol.computeContentHash("text", text)
                    if (isAutoSync && (hash == lastObservedClipHash || hash == clipboardHandler.lastCopiedFromPcHash)) {
                        return
                    }
                    lastObservedClipHash = hash
                    networkClient?.sendText(text)
                    val desc = if (isAutoSync) "Auto-synced text to PC" else "Sent text from notification action"
                    broadcastSyncEvent("$desc (${text.length} chars)")
                    Log.i("ClipboardService", "$desc: ${text.take(30)}...")
                    return
                }
            }
        } catch (e: Exception) {
            Log.d("ClipboardService", "readAndSendActiveClipboard note: ${e.message}")
        }
    }

    fun isHashSuppressed(hash: String): Boolean {
        return (networkClient?.isHashSuppressed(hash) == true) ||
                (hash == clipboardHandler.lastCopiedFromPcHash) ||
                (hash == lastObservedClipHash)
    }

    override fun onDestroy() {
        super.onDestroy()
        instance = null
        try {
            clipboardManager?.removePrimaryClipChangedListener(clipChangedListener)
        } catch (_: Exception) {}
        networkClient?.close()
        broadcastStatus(MainActivity.STATUS_DISCONNECTED)
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun broadcastStatus(status: String) {
        LocalBroadcastManager.getInstance(this).sendBroadcast(
            Intent(MainActivity.ACTION_STATUS).putExtra(MainActivity.EXTRA_STATUS, status)
        )
        updateNotification(status)
    }

    private fun broadcastSyncEvent(info: String) {
        val timestamped = "Last sync: ${timestamp()} — $info"
        LocalBroadcastManager.getInstance(this).sendBroadcast(
            Intent(MainActivity.ACTION_SYNC_EVENT).putExtra(MainActivity.EXTRA_SYNC_INFO, timestamped)
        )
    }

    private fun timestamp() =
        SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date())

    private fun updateNotification(status: String) {
        getSystemService(NotificationManager::class.java)?.notify(1, buildNotification(status))
    }

    private fun buildNotification(status: String): Notification {
        val openIntent = PendingIntent.getActivity(
            this, 0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE
        )

        // Action button to push clipboard directly from notification
        val sendActionIntent = Intent(this, ClipboardService::class.java).apply {
            action = ACTION_TRIGGER_SEND
        }
        val sendPendingIntent = PendingIntent.getService(
            this, 1, sendActionIntent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Universal Clipboard — $status")
            .setContentText("Tap to open app, or tap Send to sync clipboard")
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentIntent(openIntent)
            .addAction(R.mipmap.ic_launcher, "📋 Send to PC", sendPendingIntent)
            .setOngoing(true)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val ch = NotificationChannel(
                CHANNEL_ID, "Clipboard Sync Service",
                NotificationManager.IMPORTANCE_LOW
            )
            getSystemService(NotificationManager::class.java)?.createNotificationChannel(ch)
        }
    }
}
