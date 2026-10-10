package com.example.universalclipboard

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
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
    private val CHANNEL_ID = "ClipboardServiceChannel"

    companion object {
        // Action sent from MainActivity when it reads the clipboard in the foreground
        const val ACTION_SEND_TEXT = "com.example.universalclipboard.SEND_TEXT"
        const val EXTRA_TEXT       = "text"

        // Static reference so MainActivity can call networkClient directly
        // (avoids Android Binder 1MB limit when passing large image base64 via Intent)
        var instance: ClipboardService? = null
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
        clipboardHandler = ClipboardHandler(this)
        createNotificationChannel()
    }


    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {

        // ── Phone→Laptop: foreground clipboard send (bypasses Android 10+ block) ──
        if (intent?.action == ACTION_SEND_TEXT) {
            val text = intent.getStringExtra(EXTRA_TEXT)
            if (!text.isNullOrBlank()) {
                networkClient?.sendText(text)
                broadcastSyncEvent("Last sync: ${timestamp()} — sent text to PC")
                Log.d("ClipboardService", "Foreground send: ${text.length} chars to PC")
            }
            return START_STICKY
        }

        // ── Normal start: connect to laptop ─────────────────────────────────
        val ip    = intent?.getStringExtra("IP")
        val token = intent?.getStringExtra("TOKEN")

        if (ip != null && token != null) {
            startForeground(1, createNotification())
            broadcastStatus(MainActivity.STATUS_CONNECTING)

            networkClient?.close()
            networkClient = NetworkClient(
                context        = this,
                ip             = ip,
                port           = 8765,
                token          = token,
                onText         = { text ->
                    clipboardHandler.copyToClipboard(text)
                    broadcastSyncEvent("Last sync: ${timestamp()} — received text from PC")
                },
                onImage        = { b64 ->
                    clipboardHandler.copyImageToClipboard(b64)
                    broadcastSyncEvent("Last sync: ${timestamp()} — received image from PC")
                },
                onStatusChange = { status -> broadcastStatus(status) }
            )
            networkClient?.connect()
            Log.d("ClipboardService", "Connecting to $ip (bidirectional sync active)")
        }

        return START_STICKY
    }

    override fun onDestroy() {
        super.onDestroy()
        instance = null
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

    fun broadcastSyncEvent(info: String) {
        LocalBroadcastManager.getInstance(this).sendBroadcast(
            Intent(MainActivity.ACTION_SYNC_EVENT).putExtra(MainActivity.EXTRA_SYNC_INFO, info)
        )
    }

    private fun timestamp() =
        SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date())

    private fun updateNotification(status: String) {
        getSystemService(NotificationManager::class.java)?.notify(1, buildNotification(status))
    }

    private fun createNotification(): Notification = buildNotification("Connecting…")

    private fun buildNotification(status: String): Notification {
        val pi = PendingIntent.getActivity(
            this, 0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE
        )
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Universal Clipboard — $status")
            .setContentText("Clipboard is syncing between your devices")
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentIntent(pi)
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
