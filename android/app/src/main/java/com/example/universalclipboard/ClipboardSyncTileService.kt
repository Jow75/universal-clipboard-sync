package com.example.universalclipboard

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.os.Build
import android.service.quicksettings.TileService
import android.widget.Toast
import androidx.annotation.RequiresApi

@RequiresApi(Build.VERSION_CODES.N)
class ClipboardSyncTileService : TileService() {

    override fun onClick() {
        super.onClick()
        val serviceInstance = ClipboardService.instance
        if (serviceInstance == null || serviceInstance.networkClient == null) {
            Toast.makeText(this, "Universal Clipboard is not connected", Toast.LENGTH_SHORT).show()
            return
        }

        try {
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = clipboard.primaryClip
            if (clip != null && clip.itemCount > 0) {
                val item = clip.getItemAt(0)
                val text = item.coerceToText(this)?.toString()
                if (!text.isNullOrBlank()) {
                    serviceInstance.networkClient?.sendText(text)
                    Toast.makeText(this, "📋 Clipboard sent to PC!", Toast.LENGTH_SHORT).show()
                    return
                }
            }
            Toast.makeText(this, "Clipboard is empty", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            Toast.makeText(this, "Could not read clipboard: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }
}
