package tech.mrnothing.os

import java.util.Properties
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertNotNull
import org.junit.Test

/** Shared fixture proves Kotlin and Python emit identical canonical payload bytes. */
class OwnerConsentCanonicalizerTest {
    private fun fixture(): Pair<OwnerConsentFields, String> {
        val input = javaClass.classLoader!!.getResourceAsStream("owner-consent-v1.properties")
            ?: error("shared owner-consent fixture missing")
        val properties = Properties()
        input.use { properties.load(it) }
        val fields = OwnerConsentFields(
            version = properties.getProperty("version").toInt(),
            deviceId = properties.getProperty("device_id"),
            ownerId = properties.getProperty("owner_id"),
            sessionId = properties.getProperty("session_id"),
            action = properties.getProperty("action"),
            nonce = properties.getProperty("nonce"),
            issuedAtEpochMs = properties.getProperty("issued_at_epoch_ms").toLong(),
            expiresAtEpochMs = properties.getProperty("expires_at_epoch_ms").toLong()
        )
        return fields to properties.getProperty("canonical")
    }

    @Test fun emitsTheSharedPythonCanonicalFixtureExactly() {
        val (fields, expected) = fixture()
        assertEquals(expected, OwnerConsentCanonicalizer.canonicalPayload(fields))
    }

    @Test fun rejectsUnsupportedVersionAndAction() {
        val (fields, _) = fixture()
        assertNull(OwnerConsentCanonicalizer.canonicalPayload(fields.copy(version = 2)))
        assertNull(OwnerConsentCanonicalizer.canonicalPayload(fields.copy(action = "open_app")))
    }

    @Test fun rejectsInvalidIdentifiersAndShortNonce() {
        val (fields, _) = fixture()
        assertNull(OwnerConsentCanonicalizer.canonicalPayload(fields.copy(deviceId = "pixel\n9")))
        assertNull(OwnerConsentCanonicalizer.canonicalPayload(fields.copy(nonce = "short")))
    }

    @Test fun rejectsInvalidOrExcessiveLifetime() {
        val (fields, _) = fixture()
        assertNull(OwnerConsentCanonicalizer.canonicalPayload(
            fields.copy(expiresAtEpochMs = fields.issuedAtEpochMs)
        ))
        assertNull(OwnerConsentCanonicalizer.canonicalPayload(
            fields.copy(expiresAtEpochMs = fields.issuedAtEpochMs + 30_001L)
        ))
    }

    @Test fun acceptsSignedLongEpochBoundaryWithoutOverflow() {
        val (fields, _) = fixture()
        val boundary = fields.copy(
            issuedAtEpochMs = Long.MAX_VALUE - 30_000L,
            expiresAtEpochMs = Long.MAX_VALUE
        )
        assertNotNull(OwnerConsentCanonicalizer.canonicalPayload(boundary))
    }

    @Test fun acceptsMaximumLifetimeAndReturnsCanonicalPayload() {
        val (fields, _) = fixture()
        val maximum = fields.copy(expiresAtEpochMs = fields.issuedAtEpochMs + 30_000L)
        assertNotNull(OwnerConsentCanonicalizer.canonicalPayload(maximum))
    }
}
