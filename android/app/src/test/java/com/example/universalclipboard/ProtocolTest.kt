package com.example.universalclipboard

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ProtocolTest {

    @Test
    fun testNormalizeText() {
        val crlfText = "Hello\r\nWorld\r\n"
        val normalized = Protocol.normalizeText(crlfText)
        assertEquals("Hello\nWorld\n", normalized)
    }

    @Test
    fun testComputeContentHashConsistencyAcrossLineEndings() {
        val windowsText = "Line 1\r\nLine 2\r\n"
        val unixText = "Line 1\nLine 2\n"

        val hashWindows = Protocol.computeContentHash("text", windowsText)
        val hashUnix = Protocol.computeContentHash("text", unixText)

        assertEquals("Hashes must be identical regardless of line endings", hashWindows, hashUnix)
        assertEquals(64, hashWindows.length) // SHA-256 hex is 64 chars
    }

    @Test
    fun testComputeAuthTagDeterministic() {
        val nonce = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        val key = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"

        val tag1 = Protocol.computeAuthTag(nonce, key)
        val tag2 = Protocol.computeAuthTag(nonce, key)

        assertEquals(tag1, tag2)
        assertEquals(64, tag1.length) // HMAC-SHA256 hex is 64 chars
    }

    @Test
    fun testHexConversion() {
        val hex = "00ff107f"
        val bytes = Protocol.hexStringToByteArray(hex)
        assertEquals(4, bytes.size)
        assertEquals(0x00.toByte(), bytes[0])
        assertEquals(0xff.toByte(), bytes[1])
        assertEquals(0x10.toByte(), bytes[2])
        assertEquals(0x7f.toByte(), bytes[3])
    }
}
