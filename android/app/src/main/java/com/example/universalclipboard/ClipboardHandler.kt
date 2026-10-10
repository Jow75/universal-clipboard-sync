package com.example.universalclipboard

import android.content.ClipData
import android.content.ClipboardManager
import android.content.ContentValues
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.os.Handler
import android.os.Looper
import android.provider.MediaStore
import android.util.Base64
import android.widget.Toast
import androidx.core.content.FileProvider
import java.io.File
import java.io.FileOutputStream
import java.io.OutputStream

class ClipboardHandler(private val context: Context) {

    @Volatile
    var lastCopiedFromPcHash: String = ""

    // Handle plain text
    fun copyToClipboard(text: String) {
        lastCopiedFromPcHash = Protocol.computeContentHash("text", text)
        Handler(Looper.getMainLooper()).post {
            try {
                val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                val clip = ClipData.newPlainText("Synced from PC", text)
                clipboard.setPrimaryClip(clip)
                Toast.makeText(context, "📋 Text copied from PC", Toast.LENGTH_SHORT).show()
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    // Handle image (base64 PNG)
    fun copyImageToClipboard(base64Data: String) {
        Handler(Looper.getMainLooper()).post {
            try {
                // Decode base64 → Bitmap
                val imageBytes = Base64.decode(base64Data, Base64.DEFAULT)
                val bitmap = BitmapFactory.decodeByteArray(imageBytes, 0, imageBytes.size)
                    ?: throw Exception("Failed to decode image bytes")

                // 1. Save to FileProvider cache so third-party apps can paste without permission denial
                val providerUri = saveBitmapToFileProvider(bitmap)

                // 2. Also save to MediaStore Pictures gallery
                saveBitmapToGallery(bitmap)

                // 3. Put FileProvider URI on the clipboard
                val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                val clip = ClipData.newUri(context.contentResolver, "Synced Image from PC", providerUri)
                clipboard.setPrimaryClip(clip)

                Toast.makeText(context, "🖼️ Image copied from PC — ready to paste!", Toast.LENGTH_SHORT).show()
            } catch (e: Exception) {
                e.printStackTrace()
                Toast.makeText(context, "Image receive failed: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun saveBitmapToFileProvider(bitmap: Bitmap): Uri {
        val cacheDir = File(context.cacheDir, "clipboard").apply { mkdirs() }
        pruneOldClipboardCache(cacheDir)
        val file = File(cacheDir, "clip_${System.currentTimeMillis()}.png")
        FileOutputStream(file).use { out ->
            bitmap.compress(Bitmap.CompressFormat.PNG, 100, out)
        }
        return FileProvider.getUriForFile(
            context,
            "${context.packageName}.fileprovider",
            file
        )
    }

    private fun pruneOldClipboardCache(dir: File) {
        try {
            val files = dir.listFiles() ?: return
            val maxRetentionMs = 24 * 60 * 60 * 1000L // 24 hours
            val now = System.currentTimeMillis()
            val sorted = files.sortedByDescending { it.lastModified() }
            for ((index, file) in sorted.withIndex()) {
                if (index >= 10 || (now - file.lastModified() > maxRetentionMs)) {
                    file.delete()
                }
            }
        } catch (_: Exception) {
            // Non-critical cache pruning
        }
    }

    private fun saveBitmapToGallery(bitmap: Bitmap): Uri? {
        val filename = "clipboard_sync_${System.currentTimeMillis()}.png"
        return try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                val values = ContentValues().apply {
                    put(MediaStore.Images.Media.DISPLAY_NAME, filename)
                    put(MediaStore.Images.Media.MIME_TYPE, "image/png")
                    put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/ClipboardSync")
                    put(MediaStore.Images.Media.IS_PENDING, 1)
                }
                val resolver = context.contentResolver
                val uri = resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values) ?: return null
                resolver.openOutputStream(uri)?.use { out: OutputStream ->
                    bitmap.compress(Bitmap.CompressFormat.PNG, 100, out)
                }
                values.clear()
                values.put(MediaStore.Images.Media.IS_PENDING, 0)
                resolver.update(uri, values, null, null)
                uri
            } else {
                val dir = File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES), "ClipboardSync")
                dir.mkdirs()
                val file = File(dir, filename)
                FileOutputStream(file).use { out ->
                    bitmap.compress(Bitmap.CompressFormat.PNG, 100, out)
                }
                Uri.fromFile(file)
            }
        } catch (e: Exception) {
            null
        }
    }
}
