package com.example.universalclipboard

import android.accessibilityservice.AccessibilityService
import android.content.ClipboardManager
import android.content.Context
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
        // Window state or text selection change can also trigger clipboard check
        if (event?.eventType == AccessibilityEvent.TYPE_VIEW_TEXT_SELECTION_CHANGED ||
            event?.eventType == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) {
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
                    if (hash != lastObservedHash) {
                        lastObservedHash = hash
                        // Forward to active network client in ClipboardService
                        val client = ClipboardService.instance?.networkClient
                        if (client != null) {
                            client.sendText(text)
                            Log.i("ClipboardAccessibility", "Seamlessly sent ${text.length} chars to PC")
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
