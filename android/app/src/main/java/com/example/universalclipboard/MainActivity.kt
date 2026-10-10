package com.example.universalclipboard

import android.Manifest
import android.content.BroadcastReceiver
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
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
import com.google.zxing.integration.android.IntentIntegrator
import org.json.JSONObject

class MainActivity : AppCompatActivity() {

    // ── Setup screen widgets ─────────────────────────────────────────────────
    private lateinit var setupView: ScrollView
    private lateinit var scanQrButton: Button
    private lateinit var ipEditText: EditText
    private lateinit var tokenEditText: EditText
    private lateinit var connectButton: Button

    // ── Connected screen widgets ─────────────────────────────────────────────
    private lateinit var connectedView: LinearLayout
    private lateinit var connectedDot: View
    private lateinit var connectedStatusText: TextView
    private lateinit var connectedIpText: TextView
    private lateinit var sendNowButton: Button
    private lateinit var accessibilityButton: Button
    private lateinit var lastSyncText: TextView
    private lateinit var disconnectButton: TextView

    // ── Disconnected screen widgets ──────────────────────────────────────────
    private lateinit var disconnectedView: LinearLayout
    private lateinit var disconnectedIpText: TextView
    private lateinit var reconnectButton: Button
    private lateinit var changeDeviceButton: TextView

    private lateinit var secureStorage: SecureStorage
    private var isConnected = false
    private var lastSentHash: String = ""

    companion object {
        private const val PERMISSION_REQUEST_CAMERA = 1002
        private const val PERMISSION_REQUEST_MEDIA  = 1001

        const val ACTION_STATUS      = "com.example.universalclipboard.STATUS"
        const val ACTION_SYNC_EVENT  = "com.example.universalclipboard.SYNC_EVENT"
        const val EXTRA_STATUS       = "status"
        const val EXTRA_SYNC_INFO    = "sync_info"
        const val STATUS_CONNECTING  = "Connecting…"
        const val STATUS_CONNECTED   = "Connected"
        const val STATUS_DISCONNECTED = "Disconnected"
    }

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

        secureStorage = SecureStorage(this)

        // ── Bind views ───────────────────────────────────────────────────────
        setupView           = findViewById(R.id.setupView)
        scanQrButton        = findViewById(R.id.scanQrButton)
        ipEditText          = findViewById(R.id.ipEditText)
        tokenEditText       = findViewById(R.id.tokenEditText)
        connectButton       = findViewById(R.id.connectButton)

        connectedView       = findViewById(R.id.connectedView)
        connectedDot        = findViewById(R.id.connectedDot)
        connectedStatusText = findViewById(R.id.connectedStatusText)
        connectedIpText     = findViewById(R.id.connectedIpText)
        sendNowButton       = findViewById(R.id.sendNowButton)
        accessibilityButton = findViewById(R.id.accessibilityButton)
        lastSyncText        = findViewById(R.id.lastSyncText)
        disconnectButton    = findViewById(R.id.disconnectButton)

        disconnectedView    = findViewById(R.id.disconnectedView)
        disconnectedIpText  = findViewById(R.id.disconnectedIpText)
        reconnectButton     = findViewById(R.id.reconnectButton)
        changeDeviceButton  = findViewById(R.id.changeDeviceButton)

        requestMediaPermissions()

        // ── QR Scanner button ────────────────────────────────────────────────
        scanQrButton.setOnClickListener {
            checkCameraPermissionAndScan()
        }

        // ── Decide initial screen state ──────────────────────────────────────
        val savedIp    = secureStorage.getPairedIp()
        val savedToken = secureStorage.getPairedToken()
        val isPaired   = secureStorage.isPaired()

        if (isPaired && savedIp.isNotBlank() && !savedToken.isNullOrBlank()) {
            val deviceLabel = "${secureStorage.getPairedDeviceName()} ($savedIp)"
            showConnectedState(deviceLabel)
            startClipboardService(savedIp, savedToken)
        } else {
            showSetupState()
        }

        // ── Manual Connect button ────────────────────────────────────────────
        connectButton.setOnClickListener {
            val ip    = ipEditText.text.toString().trim()
            val token = tokenEditText.text.toString().trim()
            if (ip.isBlank() || token.isBlank()) {
                Toast.makeText(this, "Enter both IP and Pairing Token, or Scan QR Code", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            secureStorage.savePairing(ip, 8765, token, "Windows PC", "manual")
            showConnectedState("Windows PC ($ip)")
            startClipboardService(ip, token)
        }

        // ── Disconnect button ────────────────────────────────────────────────
        disconnectButton.setOnClickListener {
            val dev = secureStorage.getPairedDeviceName()
            AlertDialog.Builder(this)
                .setTitle("Disconnect")
                .setMessage("Are you sure you want to disconnect from $dev?")
                .setPositiveButton("Disconnect") { _, _ ->
                    stopService(Intent(this, ClipboardService::class.java))
                    isConnected = false
                    secureStorage.clearPairing()
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

        // ── Reconnect button ─────────────────────────────────────────────────
        reconnectButton.setOnClickListener {
            val ip    = secureStorage.getPairedIp()
            val token = secureStorage.getPairedToken()
            if (ip.isNotBlank() && !token.isNullOrBlank()) {
                val dev = "${secureStorage.getPairedDeviceName()} ($ip)"
                showConnectedState(dev)
                startClipboardService(ip, token)
            } else {
                showSetupState()
            }
        }

        // ── Change Device button ─────────────────────────────────────────────
        changeDeviceButton.setOnClickListener {
            secureStorage.clearPairing()
            stopService(Intent(this, ClipboardService::class.java))
            isConnected = false
            showSetupState()
        }
    }

    private fun checkCameraPermissionAndScan() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
            == PackageManager.PERMISSION_GRANTED) {
            launchQrScanner()
        } else {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.CAMERA),
                PERMISSION_REQUEST_CAMERA
            )
        }
    }

    private fun launchQrScanner() {
        val integrator = IntentIntegrator(this)
        integrator.setPrompt("Point your camera at the QR code on your PC screen")
        integrator.setBeepEnabled(false)
        integrator.setOrientationLocked(false)
        integrator.setDesiredBarcodeFormats(IntentIntegrator.QR_CODE)
        integrator.initiateScan()
    }

    override fun onRequestPermissionsResult(
        requestCode: Int, permissions: Array<out String>, grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQUEST_CAMERA) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                launchQrScanner()
            } else {
                Toast.makeText(this, "Camera permission is required to scan QR code", Toast.LENGTH_LONG).show()
            }
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        val result = IntentIntegrator.parseActivityResult(requestCode, resultCode, data)
        if (result != null) {
            if (result.contents != null) {
                handleScannedQrCode(result.contents)
            }
            return
        }
        super.onActivityResult(requestCode, resultCode, data)
    }

    private fun handleScannedQrCode(qrContents: String) {
        try {
            val json = JSONObject(qrContents)
            val action = json.optString("action")
            val ip = json.optString("ip")
            val port = json.optInt("port", 8765)
            val token = json.optString("token")
            val exp = json.optLong("exp", 0)
            val name = json.optString("name", "Windows PC")
            val id = json.optString("id", "")

            if (action != "pair" || ip.isBlank() || token.isBlank()) {
                Toast.makeText(this, "Invalid QR code format for Universal Clipboard", Toast.LENGTH_LONG).show()
                return
            }

            // Verify expiration
            val nowSec = System.currentTimeMillis() / 1000
            if (exp > 0 && nowSec > exp) {
                Toast.makeText(this, "⚠️ QR Code has expired. Open a new QR code on your PC.", Toast.LENGTH_LONG).show()
                return
            }

            // Save credentials securely
            secureStorage.savePairing(ip, port, token, name, id)
            showConnectedState("$name ($ip)")
            startClipboardService(ip, token)

            Toast.makeText(this, "✅ Paired with $name successfully!", Toast.LENGTH_SHORT).show()

        } catch (e: Exception) {
            Log.e("MainActivity", "Error parsing QR code: ${e.message}")
            Toast.makeText(this, "Failed to parse QR code: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }

    override fun onResume() {
        super.onResume()
        val filter = IntentFilter().apply {
            addAction(ACTION_STATUS)
            addAction(ACTION_SYNC_EVENT)
        }
        LocalBroadcastManager.getInstance(this).registerReceiver(statusReceiver, filter)

        updateAccessibilityButton()

        if (isConnected) {
            sendCurrentClipboardToLaptop()
        }
    }

    private fun isAccessibilityServiceEnabled(): Boolean {
        return try {
            val enabledServices = android.provider.Settings.Secure.getString(
                contentResolver,
                android.provider.Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
            ) ?: return false
            enabledServices.contains(packageName)
        } catch (_: Exception) {
            false
        }
    }

    private fun updateAccessibilityButton() {
        if (isAccessibilityServiceEnabled()) {
            accessibilityButton.text = "⚡ Seamless Auto-Sync: Active"
            accessibilityButton.setTextColor(Color.parseColor("#00DD88"))
            accessibilityButton.setOnClickListener {
                Toast.makeText(this, "Seamless background sync is active! Copied text syncs automatically.", Toast.LENGTH_SHORT).show()
            }
        } else {
            accessibilityButton.text = "⚡ Enable Seamless Auto-Sync (No Taps)"
            accessibilityButton.setTextColor(Color.parseColor("#FFAA00"))
            accessibilityButton.setOnClickListener {
                try {
                    startActivity(Intent(android.provider.Settings.ACTION_ACCESSIBILITY_SETTINGS))
                    Toast.makeText(this, "Enable 'Universal Clipboard Sync' to sync copied text without opening the app", Toast.LENGTH_LONG).show()
                } catch (e: Exception) {
                    Toast.makeText(this, "Open Android Settings → Accessibility → Universal Clipboard Sync", Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    override fun onPause() {
        super.onPause()
        LocalBroadcastManager.getInstance(this).unregisterReceiver(statusReceiver)
    }

    private fun showSetupState() {
        setupView.visibility        = View.VISIBLE
        connectedView.visibility    = View.GONE
        disconnectedView.visibility = View.GONE
    }

    private fun showConnectedState(deviceLabel: String) {
        setupView.visibility        = View.GONE
        connectedView.visibility    = View.VISIBLE
        disconnectedView.visibility = View.GONE

        connectedIpText.text     = deviceLabel
        connectedStatusText.text = "Connected"
        connectedStatusText.setTextColor(Color.parseColor("#00DD88"))
        connectedDot.setBackgroundResource(R.drawable.bg_dot_connected)

        val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
        imm.hideSoftInputFromWindow(currentFocus?.windowToken ?: window.decorView.windowToken, 0)
    }

    private fun showDisconnectedState(deviceLabel: String) {
        setupView.visibility        = View.GONE
        connectedView.visibility    = View.GONE
        disconnectedView.visibility = View.VISIBLE

        disconnectedIpText.text = deviceLabel
    }

    private fun handleStatusChange(status: String) {
        val dev = "${secureStorage.getPairedDeviceName()} (${secureStorage.getPairedIp()})"
        val isPaired = secureStorage.isPaired()

        when (status) {
            STATUS_CONNECTED -> {
                isConnected = true
                showConnectedState(dev)
            }
            STATUS_CONNECTING -> {
                if (connectedView.visibility == View.VISIBLE) {
                    connectedStatusText.text = "Connecting…"
                    connectedStatusText.setTextColor(Color.parseColor("#FFAA00"))
                    connectedDot.setBackgroundResource(R.drawable.bg_dot_connecting)
                }
            }
            STATUS_DISCONNECTED -> {
                isConnected = false
                if (isPaired) {
                    showDisconnectedState(dev)
                }
            }
        }
    }

    private fun startClipboardService(ip: String, token: String) {
        val intent = Intent(this, ClipboardService::class.java).apply {
            putExtra("IP", ip)
            putExtra("TOKEN", token)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(intent)
        } else {
            startService(intent)
        }
    }

    private fun sendCurrentClipboardToLaptop() {
        if (!isConnected) return
        try {
            val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            val clip = clipboard.primaryClip ?: return
            val item = clip.getItemAt(0) ?: return
            val client = ClipboardService.instance?.networkClient ?: return

            // ── Image in clipboard ──
            val uri = item.uri
            val mimeType = if (clip.description.mimeTypeCount > 0) clip.description.getMimeType(0) ?: "" else ""
            if (uri != null && mimeType.startsWith("image/")) {
                Thread {
                    try {
                        val hash = uri.toString()
                        if (hash == lastSentHash) return@Thread
                        lastSentHash = hash

                        contentResolver.openInputStream(uri)?.use { stream: java.io.InputStream ->
                            val bitmap = android.graphics.BitmapFactory.decodeStream(stream)
                                ?: return@Thread

                            val maxDim = Math.max(bitmap.width, bitmap.height)
                            val scaled = if (maxDim > 1280) {
                                val ratio = 1280f / maxDim
                                android.graphics.Bitmap.createScaledBitmap(
                                    bitmap,
                                    (bitmap.width * ratio).toInt(),
                                    (bitmap.height * ratio).toInt(),
                                    true
                                )
                            } else bitmap

                            val output = java.io.ByteArrayOutputStream()
                            scaled.compress(android.graphics.Bitmap.CompressFormat.JPEG, 75, output)
                            val base64 = android.util.Base64.encodeToString(
                                output.toByteArray(), android.util.Base64.NO_WRAP
                            )
                            client.sendImage(base64)
                        }

                        runOnUiThread {
                            lastSyncText.text = "Sent image to PC"
                            Toast.makeText(this, "Image sent to PC!", Toast.LENGTH_SHORT).show()
                        }
                    } catch (e: Exception) {
                        Log.e("MainActivity", "Image send failed: ${e.message}")
                    }
                }.start()
                return
            }

            // ── Text in clipboard ──
            val text = item.coerceToText(this)?.toString()
            if (text.isNullOrBlank()) return
            val hash = Protocol.computeContentHash("text", text)
            if (hash == lastSentHash) return
            lastSentHash = hash

            client.sendText(text)
            lastSyncText.text = "Sent text to PC"
            Toast.makeText(this, "Clipboard sent to PC!", Toast.LENGTH_SHORT).show()

        } catch (e: Exception) {
            Log.e("MainActivity", "sendCurrentClipboardToLaptop error: ${e.message}")
        }
    }

    private fun requestMediaPermissions() {
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
            ActivityCompat.requestPermissions(this, permissions.toTypedArray(), PERMISSION_REQUEST_MEDIA)
    }
}
