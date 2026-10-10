package com.example.universalclipboard

import android.Manifest
import android.content.BroadcastReceiver
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.SharedPreferences
import android.content.pm.PackageManager
import android.graphics.Color
import android.os.Build
import android.os.Bundle
import android.view.View
import android.view.inputmethod.InputMethodManager
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.util.Log
import android.widget.ScrollView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.localbroadcastmanager.content.LocalBroadcastManager

class MainActivity : AppCompatActivity() {

    // ── Setup screen widgets ─────────────────────────────────────────────────
    private lateinit var setupView: ScrollView
    private lateinit var ipEditText: EditText
    private lateinit var tokenEditText: EditText
    private lateinit var connectButton: Button

    // ── Connected screen widgets ─────────────────────────────────────────────
    private lateinit var connectedView: LinearLayout
    private lateinit var connectedDot: View
    private lateinit var connectedStatusText: TextView
    private lateinit var connectedIpText: TextView
    private lateinit var sendNowButton: Button
    private lateinit var lastSyncText: TextView
    private lateinit var disconnectButton: TextView

    // ── Disconnected screen widgets ──────────────────────────────────────────
    private lateinit var disconnectedView: LinearLayout
    private lateinit var disconnectedIpText: TextView
    private lateinit var reconnectButton: Button
    private lateinit var changeDeviceButton: TextView

    private lateinit var prefs: SharedPreferences
    private var isConnected = false
    private var lastSentHash: String = ""

    companion object {
        private const val PERMISSION_REQUEST_CODE = 1001
        const val ACTION_STATUS      = "com.example.universalclipboard.STATUS"
        const val ACTION_SYNC_EVENT  = "com.example.universalclipboard.SYNC_EVENT"
        const val EXTRA_STATUS       = "status"
        const val EXTRA_SYNC_INFO    = "sync_info"
        const val STATUS_CONNECTING  = "Connecting…"
        const val STATUS_CONNECTED   = "Connected"
        const val STATUS_DISCONNECTED = "Disconnected"
        private const val PREFS_NAME  = "clipboard_prefs"
        private const val KEY_IP      = "last_ip"
        private const val KEY_TOKEN   = "last_token"
        private const val KEY_PAIRED  = "is_paired"
    }

    // ── Broadcast receiver for service → activity status updates ─────────────
    private val statusReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            when (intent.action) {
                ACTION_STATUS -> {
                    val status = intent.getStringExtra(EXTRA_STATUS) ?: return
                    handleStatusChange(status)
                }
                ACTION_SYNC_EVENT -> {
                    val info = intent.getStringExtra(EXTRA_SYNC_INFO) ?: return
                    lastSyncText.text = info
                }
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        window.statusBarColor = Color.parseColor("#0D1B2A")
        window.navigationBarColor = Color.parseColor("#0D1B2A")

        prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

        // ── Bind views ───────────────────────────────────────────────────────
        setupView           = findViewById(R.id.setupView)
        ipEditText          = findViewById(R.id.ipEditText)
        tokenEditText       = findViewById(R.id.tokenEditText)
        connectButton       = findViewById(R.id.connectButton)

        connectedView       = findViewById(R.id.connectedView)
        connectedDot        = findViewById(R.id.connectedDot)
        connectedStatusText = findViewById(R.id.connectedStatusText)
        connectedIpText     = findViewById(R.id.connectedIpText)
        sendNowButton       = findViewById(R.id.sendNowButton)
        lastSyncText        = findViewById(R.id.lastSyncText)
        disconnectButton    = findViewById(R.id.disconnectButton)

        disconnectedView    = findViewById(R.id.disconnectedView)
        disconnectedIpText  = findViewById(R.id.disconnectedIpText)
        reconnectButton     = findViewById(R.id.reconnectButton)
        changeDeviceButton  = findViewById(R.id.changeDeviceButton)

        requestImagePermissions()

        // ── Restore saved fields ─────────────────────────────────────────────
        ipEditText.setText(prefs.getString(KEY_IP, ""))
        tokenEditText.setText(prefs.getString(KEY_TOKEN, ""))

        // ── Decide initial screen state ──────────────────────────────────────
        val savedIp    = prefs.getString(KEY_IP, "") ?: ""
        val savedToken = prefs.getString(KEY_TOKEN, "") ?: ""
        val wasPaired  = prefs.getBoolean(KEY_PAIRED, false)

        if (wasPaired && savedIp.isNotBlank() && savedToken.isNotBlank()) {
            // Auto-reconnect: go straight to connected screen & start service
            isConnected = true
            showConnectedState(savedIp)
            startClipboardService(savedIp, savedToken)
        } else {
            showSetupState()
        }

        // ── Connect button ───────────────────────────────────────────────────
        connectButton.setOnClickListener {
            val ip    = ipEditText.text.toString().trim()
            val token = tokenEditText.text.toString().trim()
            if (ip.isBlank() || token.isBlank()) {
                Toast.makeText(this, "Enter both IP and Pairing Token", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            prefs.edit()
                .putString(KEY_IP, ip)
                .putString(KEY_TOKEN, token)
                .putBoolean(KEY_PAIRED, true)
                .apply()

            isConnected = true
            showConnectedState(ip)
            startClipboardService(ip, token)
        }

        // ── Disconnect (with confirmation) ───────────────────────────────────
        disconnectButton.setOnClickListener {
            val ip = prefs.getString(KEY_IP, "") ?: ""
            AlertDialog.Builder(this)
                .setTitle("Disconnect")
                .setMessage("Are you sure you want to disconnect from $ip?")
                .setPositiveButton("Disconnect") { _, _ ->
                    stopService(Intent(this, ClipboardService::class.java))
                    isConnected = false
                    prefs.edit().putBoolean(KEY_PAIRED, false).apply()
                    showSetupState()
                    lastSyncText.text = "No sync yet"
                    lastSentHash = ""
                }
                .setNegativeButton("Cancel", null)
                .show()
        }

        // ── Send Now button ──────────────────────────────────────────────────
        sendNowButton.setOnClickListener {
            sendCurrentClipboardToLaptop()
        }

        // ── Reconnect button (disconnected screen) ──────────────────────────
        reconnectButton.setOnClickListener {
            val ip    = prefs.getString(KEY_IP, "") ?: ""
            val token = prefs.getString(KEY_TOKEN, "") ?: ""
            if (ip.isNotBlank() && token.isNotBlank()) {
                isConnected = true
                prefs.edit().putBoolean(KEY_PAIRED, true).apply()
                showConnectedState(ip)
                startClipboardService(ip, token)
            } else {
                showSetupState()
            }
        }

        // ── Change Device (disconnected screen → setup) ─────────────────────
        changeDeviceButton.setOnClickListener {
            prefs.edit().putBoolean(KEY_PAIRED, false).apply()
            stopService(Intent(this, ClipboardService::class.java))
            isConnected = false
            showSetupState()
        }
    }

    // ── Lifecycle ────────────────────────────────────────────────────────────

    override fun onResume() {
        super.onResume()
        val filter = IntentFilter().apply {
            addAction(ACTION_STATUS)
            addAction(ACTION_SYNC_EVENT)
        }
        LocalBroadcastManager.getInstance(this).registerReceiver(statusReceiver, filter)

        // Auto-send on resume if connected
        if (isConnected) {
            sendCurrentClipboardToLaptop()
        }
    }

    override fun onPause() {
        super.onPause()
        LocalBroadcastManager.getInstance(this).unregisterReceiver(statusReceiver)
    }

    // ── Screen state management ──────────────────────────────────────────────

    private fun showSetupState() {
        setupView.visibility        = View.VISIBLE
        connectedView.visibility    = View.GONE
        disconnectedView.visibility = View.GONE
    }

    private fun showConnectedState(ip: String) {
        setupView.visibility        = View.GONE
        connectedView.visibility    = View.VISIBLE
        disconnectedView.visibility = View.GONE

        connectedIpText.text     = ip
        connectedStatusText.text = "Connected"
        connectedStatusText.setTextColor(Color.parseColor("#00DD88"))
        connectedDot.setBackgroundResource(R.drawable.bg_dot_connected)

        // Dismiss keyboard & clear focus from any edit text
        val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
        imm.hideSoftInputFromWindow(currentFocus?.windowToken ?: window.decorView.windowToken, 0)
        ipEditText.clearFocus()
        tokenEditText.clearFocus()
    }

    private fun showDisconnectedState(ip: String) {
        setupView.visibility        = View.GONE
        connectedView.visibility    = View.GONE
        disconnectedView.visibility = View.VISIBLE

        disconnectedIpText.text = ip
    }

    /**
     * Called when a status broadcast arrives from the service.
     * Automatically transitions between Connected / Disconnected screens.
     */
    private fun handleStatusChange(status: String) {
        val savedIp = prefs.getString(KEY_IP, "") ?: ""
        val isPaired = prefs.getBoolean(KEY_PAIRED, false)

        when (status) {
            STATUS_CONNECTED -> {
                isConnected = true
                showConnectedState(savedIp)
            }
            STATUS_CONNECTING -> {
                // While connecting, update the pill text (stay on connected screen)
                if (connectedView.visibility == View.VISIBLE) {
                    connectedStatusText.text = "Connecting…"
                    connectedStatusText.setTextColor(Color.parseColor("#FFAA00"))
                    connectedDot.setBackgroundResource(R.drawable.bg_dot_connecting)
                }
            }
            STATUS_DISCONNECTED -> {
                isConnected = false
                if (isPaired) {
                    // Connection was lost mid-session — offer reconnect
                    showDisconnectedState(savedIp)
                }
                // If not paired we're already on setup screen, stay there
            }
        }
    }

    // ── Helper: start ClipboardService ───────────────────────────────────────

    private fun startClipboardService(ip: String, token: String) {
        val intent = Intent(this, ClipboardService::class.java).apply {
            putExtra("IP", ip)
            putExtra("TOKEN", token)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) startForegroundService(intent)
        else startService(intent)
    }

    // ── Clipboard send logic (unchanged) ─────────────────────────────────────

    /**
     * Reads the clipboard while this Activity is in the FOREGROUND (works on Android 10+).
     * Handles both text and image content.
     */
    private fun sendCurrentClipboardToLaptop() {
        if (!isConnected) return
        try {
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = clipboard.primaryClip ?: return
            val item = clip.getItemAt(0) ?: return
            val client = ClipboardService.instance?.networkClient ?: return

            // ── Image in clipboard? ──────────────────────────────────────────
            val uri = item.uri
            val mimeType = clip.description.getMimeType(0) ?: ""
            if (uri != null && mimeType.startsWith("image/")) {
                Thread {
                    try {
                        val hash = uri.toString()
                        if (hash == lastSentHash) return@Thread
                        lastSentHash = hash

                        contentResolver.openInputStream(uri)?.use { stream: java.io.InputStream ->
                            val bitmap = android.graphics.BitmapFactory.decodeStream(stream)
                                ?: return@Thread

                            val scaled = if (bitmap.width > 1280) {
                                val ratio = 1280f / bitmap.width
                                android.graphics.Bitmap.createScaledBitmap(
                                    bitmap,
                                    1280,
                                    (bitmap.height * ratio).toInt(),
                                    true
                                )
                            } else bitmap

                            val output = java.io.ByteArrayOutputStream()
                            scaled.compress(android.graphics.Bitmap.CompressFormat.JPEG, 70, output)
                            val base64 = android.util.Base64.encodeToString(
                                output.toByteArray(), android.util.Base64.NO_WRAP
                            )
                            client.sendImage(base64)
                            Log.d("MainActivity", "Sent image to PC (${output.size()} bytes)")
                        }

                        runOnUiThread {
                            lastSyncText.text = "Sent image to PC just now"
                            Toast.makeText(this, "Image sent to PC!", Toast.LENGTH_SHORT).show()
                        }
                    } catch (e: Exception) {
                        Log.e("MainActivity", "Image send failed: ${e.message}")
                        runOnUiThread {
                            Toast.makeText(this, "Could not send image: ${e.message}", Toast.LENGTH_SHORT).show()
                        }
                    }
                }.start()
                return
            }

            // ── Text in clipboard ────────────────────────────────────────────
            val text = item.coerceToText(this)?.toString()
            if (text.isNullOrBlank()) return
            val hash = text.hashCode().toString()
            if (hash == lastSentHash) return
            lastSentHash = hash

            client.sendText(text)
            lastSyncText.text = "Sent text to PC just now"
            Toast.makeText(this, "Clipboard sent to PC!", Toast.LENGTH_SHORT).show()

        } catch (e: Exception) {
            Log.e("MainActivity", "sendCurrentClipboardToLaptop error: ${e.message}")
        }
    }

    // ── Permissions ──────────────────────────────────────────────────────────

    private fun requestImagePermissions() {
        val permissions = mutableListOf<String>()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_MEDIA_IMAGES)
                != PackageManager.PERMISSION_GRANTED)
                permissions.add(Manifest.permission.READ_MEDIA_IMAGES)
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED)
                permissions.add(Manifest.permission.POST_NOTIFICATIONS)
        } else if (Build.VERSION.SDK_INT <= Build.VERSION_CODES.P) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE)
                != PackageManager.PERMISSION_GRANTED)
                permissions.add(Manifest.permission.WRITE_EXTERNAL_STORAGE)
        }
        if (permissions.isNotEmpty())
            ActivityCompat.requestPermissions(this, permissions.toTypedArray(), PERMISSION_REQUEST_CODE)
    }
}
