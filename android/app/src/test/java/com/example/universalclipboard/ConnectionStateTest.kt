package com.example.universalclipboard

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ConnectionStateTest {

    @Test
    fun testConnectionStateValues() {
        val states = ConnectionState.values().map { it.name }
        assertTrue(states.contains("DISCONNECTED"))
        assertTrue(states.contains("DISCOVERING"))
        assertTrue(states.contains("CONNECTING"))
        assertTrue(states.contains("AUTHENTICATING"))
        assertTrue(states.contains("CONNECTED"))
        assertTrue(states.contains("RECONNECTING"))
        assertTrue(states.contains("ERROR"))
    }

    @Test
    fun testContentHashMatchesExpectedLength() {
        val hash = Protocol.computeContentHash("text", "Test content")
        assertEquals(64, hash.length)
    }

    @Test
    fun testNormalizeTextPreservesUnix() {
        val unix = "alpha\nbeta\n"
        assertEquals(unix, Protocol.normalizeText(unix))
    }
}
