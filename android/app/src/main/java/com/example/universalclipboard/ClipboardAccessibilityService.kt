package com.example.universalclipboard

import android.accessibilityservice.AccessibilityService
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import android.view.accessibility.AccessibilityEvent

/**
 * Android Accessibility Service enabling seamless background clipboard synchronization
 * across all Android applications on Android 10+ (API 29+) without requiring foreground focus.
 */
class ClipboardAccessibilityService : AccessibilityService() {

    private var clipboardManager: ClipboardManager? = null
    private var lastObservedHash: String = ""

    private val clipListener = ClipboardManager.OnPrimaryClipChangedListener {
        handleClipboardChanged()
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        Log.i("ClipboardAccessibility", "Accessibility Service connected and ready")
        clipboardManager = getSystemService(Context.CLIPBOARD_SERVICE) as? ClipboardManager
        try {
            clipboardManager?.addPrimaryClipChangedListener(clipListener)
        } catch (e: Exception) {
            Log.w("ClipboardAccessibility", "Failed to register clipListener: ${e.message}")
        }
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Any interaction that could represent copying or changing selection triggers clipboard check
        val evtType = event?.eventType
        if (evtType == AccessibilityEvent.TYPE_VIEW_TEXT_SELECTION_CHANGED ||
            evtType == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED ||
            evtType == AccessibilityEvent.TYPE_VIEW_CLICKED ||
            evtType == AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED) {
            handleClipboardChanged()
        }
    }

    override fun onInterrupt() {
        Log.i("ClipboardAccessibility", "Accessibility Service interrupted")
    }

    private fun handleClipboardChanged() {
        try {
            val clip = clipboardManager?.primaryClip ?: return
            if (clip.itemCount > 0) {
                val item = clip.getItemAt(0)
                val text = item.coerceToText(this)?.toString()
                if (!text.isNullOrBlank()) {
                    val hash = Protocol.computeContentHash("text", text)

                    // Suppress duplicate or echo-loop reflections
                    val service = ClipboardService.instance
                    if (service != null && service.isHashSuppressed(hash)) {
                        return
                    }

                    if (hash != lastObservedHash) {
                        lastObservedHash = hash

                        if (service?.networkClient != null && service.networkClient?.isConnectedAndAuthenticated() == true) {
                            service.networkClient?.sendText(text)
                            Log.i("ClipboardAccessibility", "Seamlessly sent ${text.length} chars to PC via active client")
                        } else {
                            // Forward via Intent to ClipboardService
                            val intent = Intent(this, ClipboardService::class.java).apply {
                                action = ClipboardService.ACTION_SEND_TEXT
                                putExtra(ClipboardService.EXTRA_TEXT, text)
                            }
                            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                                startForegroundService(intent)
                            } else {
                                startService(intent)
                            }
                            Log.i("ClipboardAccessibility", "Forwarded ${text.length} chars to ClipboardService intent")
                        }
                    }
                }
            }
        } catch (e: Exception) {
            Log.d("ClipboardAccessibility", "Clipboard check note: ${e.message}")
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        try {
            clipboardManager?.removePrimaryClipChangedListener(clipListener)
        } catch (_: Exception) {}
        Log.i("ClipboardAccessibility", "Accessibility Service destroyed")
    }
}
