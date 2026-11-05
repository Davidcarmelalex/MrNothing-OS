package tech.mrnothing.os

import java.util.Base64
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertNotNull
import org.junit.Test

/** Pure envelope tests; these do not claim to exercise AndroidKeyStore or StrongBox. */
class OwnerConsentSignerTest {
    private val fields = OwnerConsentFields(
        version = 1,
        deviceId = "pixel9pro-test",
        ownerId = "owner-test",
        sessionId = "session-test",
        action = "read_screen",
        nonce = "0123456789abcdef0123456789abcdef",
        issuedAtEpochMs = 1_700_000_000_000L,
        expiresAtEpochMs = 1_700_000_030_000L
    )

    private val syntheticDerSignature = byteArrayOf(
        0x30, 0x06, 0x02, 0x01, 0x01, 0x02, 0x01, 0x01
    )

    @Test
    fun envelopeContainsExactCanonicalPayloadAndUnpaddedBase64UrlSignature() {
        val canonical = OwnerConsentCanonicalizer.canonicalPayload(fields)
        val encodedSignature = Base64.getUrlEncoder()
            .withoutPadding()
            .encodeToString(syntheticDerSignature)

        val envelope = OwnerConsentSigner.encodeEnvelope(fields, syntheticDerSignature)

        assertNotNull(envelope)
        assertEquals(
            "{\"payload\":$canonical,\"signature\":\"$encodedSignature\"}",
            envelope
        )
        assertFalse(envelope!!.contains("="))
    }

    @Test
    fun rejectsEmptyTooShortAndOversizedDerSignatures() {
        assertNull(OwnerConsentSigner.encodeEnvelope(fields, byteArrayOf()))
        assertNull(OwnerConsentSigner.encodeEnvelope(fields, ByteArray(7)))
        assertNull(OwnerConsentSigner.encodeEnvelope(fields, ByteArray(73)))
    }

    @Test
    fun refusesInvalidChallengeBeforeBuildingEnvelope() {
        val invalid = fields.copy(action = "open_app")
        assertNull(OwnerConsentSigner.encodeEnvelope(invalid, syntheticDerSignature))
    }
}
