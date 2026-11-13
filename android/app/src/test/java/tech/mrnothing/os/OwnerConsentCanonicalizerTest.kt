package tech.mrnothing.os

import java.util.Properties
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertNotNull
import org.junit.Test

/** Shared fixtures prove Kotlin and Python emit identical canonical payload bytes. */
class OwnerConsentCanonicalizerTest {
    private fun properties(name: String): Properties {
        val input = javaClass.classLoader!!.getResourceAsStream(name)
            ?: error("shared owner-consent fixture missing: $name")
        return Properties().also { props -> input.use { props.load(it) } }
    }

    private fun v1Fixture(): Pair<OwnerConsentFields, String> {
        val p = properties("owner-consent-v1.properties")
        val fields = OwnerConsentFields(
            version = p.getProperty("version").toInt(),
            deviceId = p.getProperty("device_id"),
            ownerId = p.getProperty("owner_id"),
            sessionId = p.getProperty("session_id"),
            action = p.getProperty("action"),
            nonce = p.getProperty("nonce"),
            issuedAtEpochMs = p.getProperty("issued_at_epoch_ms").toLong(),
            expiresAtEpochMs = p.getProperty("expires_at_epoch_ms").toLong()
        )
        return fields to p.getProperty("canonical")
    }

    private fun v2Fixture(): Pair<OwnerConsentFields, String> {
        val p = properties("owner-consent-v2.properties")
        val fields = OwnerConsentFields(
            version = p.getProperty("version").toInt(),
            deviceId = p.getProperty("device_id"),
            ownerId = p.getProperty("owner_id"),
            sessionId = p.getProperty("session_id"),
            action = p.getProperty("action"),
            nonce = p.getProperty("nonce"),
            issuedAtEpochMs = p.getProperty("issued_at_epoch_ms").toLong(),
            expiresAtEpochMs = p.getProperty("expires_at_epoch_ms").toLong(),
            arguments = OwnerActionArguments.Navigate(p.getProperty("target_package")),
            argumentsSha256 = p.getProperty("arguments_sha256")
        )
        return fields to p.getProperty("canonical")
    }

    @Test fun emitsTheSharedPythonV1CanonicalFixtureExactly() {
        val (fields, expected) = v1Fixture()
        assertEquals(expected, OwnerConsentCanonicalizer.canonicalPayload(fields))
    }

    @Test fun emitsTheSharedPythonV2CanonicalFixtureExactly() {
        val (fields, expected) = v2Fixture()
        assertEquals(expected, OwnerConsentCanonicalizer.canonicalPayload(fields))
        val p = properties("owner-consent-v2.properties")
        assertEquals(
            p.getProperty("arguments_sha256"),
            OwnerActionArgumentsCanonicalizer.sha256(fields.action, fields.arguments)
        )
        assertEquals(
            p.getProperty("arguments_json"),
            OwnerActionArgumentsCanonicalizer.canonicalJson(fields.action, fields.arguments)
        )
    }

    @Test fun rejectsUnsupportedVersionAndAction() {
        val (fields, _) = v1Fixture()
        assertNull(OwnerConsentCanonicalizer.canonicalPayload(fields.copy(version = 3)))
        assertNull(OwnerConsentCanonicalizer.canonicalPayload(fields.copy(action = "open_app")))
    }

    @Test fun rejectsV2ArgumentDigestMismatchAndInvalidArgumentSchema() {
        val (fields, _) = v2Fixture()
        assertNull(OwnerConsentCanonicalizer.canonicalPayload(
            fields.copy(argumentsSha256 = "0".repeat(64))
        ))
        assertNull(OwnerConsentCanonicalizer.canonicalPayload(
            fields.copy(arguments = OwnerActionArguments.Navigate("com.example notes"))
        ))
        assertNull(OwnerActionArgumentsCanonicalizer.canonicalJson(
            "scroll", OwnerActionArguments.Scroll("sideways", 100)
        ))
        assertNull(OwnerActionArgumentsCanonicalizer.canonicalJson(
            "scroll", OwnerActionArguments.Scroll("down", 0)
        ))
    }

    @Test fun rejectsInvalidIdentifiersAndShortNonce() {
        val (fields, _) = v1Fixture()
        assertNull(OwnerConsentCanonicalizer.canonicalPayload(fields.copy(deviceId = "pixel\n9")))
        assertNull(OwnerConsentCanonicalizer.canonicalPayload(fields.copy(nonce = "short")))
    }

    @Test fun rejectsInvalidOrExcessiveLifetime() {
        val (fields, _) = v1Fixture()
        assertNull(OwnerConsentCanonicalizer.canonicalPayload(
            fields.copy(expiresAtEpochMs = fields.issuedAtEpochMs)
        ))
        assertNull(OwnerConsentCanonicalizer.canonicalPayload(
            fields.copy(expiresAtEpochMs = fields.issuedAtEpochMs + 30_001L)
        ))
    }

    @Test fun acceptsSignedLongEpochBoundaryWithoutOverflow() {
        val (fields, _) = v1Fixture()
        val boundary = fields.copy(
            issuedAtEpochMs = Long.MAX_VALUE - 30_000L,
            expiresAtEpochMs = Long.MAX_VALUE
        )
        assertNotNull(OwnerConsentCanonicalizer.canonicalPayload(boundary))
    }

    @Test fun acceptsMaximumLifetimeAndReturnsCanonicalPayload() {
        val (fields, _) = v1Fixture()
        val maximum = fields.copy(expiresAtEpochMs = fields.issuedAtEpochMs + 30_000L)
        assertNotNull(OwnerConsentCanonicalizer.canonicalPayload(maximum))
    }
}
