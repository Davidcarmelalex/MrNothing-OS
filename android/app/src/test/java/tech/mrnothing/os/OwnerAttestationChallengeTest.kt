package tech.mrnothing.os

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Assert.assertEquals
import org.junit.Test

/** Synthetic DER only; NOT an Android emulator, hardware or PKI test. */
class OwnerAttestationChallengeTest {
    private val challenge = ByteArray(32) { it.toByte() }

    private fun der(tag: Int, value: ByteArray): ByteArray {
        val len = when {
            value.size < 128 -> byteArrayOf(value.size.toByte())
            value.size < 256 -> byteArrayOf(0x81.toByte(), value.size.toByte())
            else -> byteArrayOf(0x82.toByte(), (value.size shr 8).toByte(), value.size.toByte())
        }
        return byteArrayOf(tag.toByte()) + len + value
    }

    private fun extension(
        nonce: ByteArray = challenge,
        attestationLevel: Int = 2,
        keymasterLevel: Int = 2
    ): ByteArray {
        val fields = der(2, byteArrayOf(4)) +
            der(10, byteArrayOf(attestationLevel.toByte())) +
            der(2, byteArrayOf(4)) +
            der(10, byteArrayOf(keymasterLevel.toByte())) +
            der(4, nonce) + der(4, byteArrayOf()) +
            der(0x30, byteArrayOf()) + der(0x30, byteArrayOf())
        return der(4, der(0x30, fields))
    }

    @Test fun generatedChallengesAreFreshAndCorrectLength() {
        val first = OwnerAttestationChallenge.create()
        val second = OwnerAttestationChallenge.create()
        assertEquals(32, first.size)
        assertEquals(32, second.size)
        assertFalse(first.contentEquals(second))
    }

    @Test fun matchingSyntheticStrongBoxExtensionIsAcceptedLocally() =
        assertTrue(OwnerAttestationChallenge.matchesLocalEvidence(extension(), challenge))

    @Test fun wrongChallengeIsDenied() =
        assertFalse(OwnerAttestationChallenge.matchesLocalEvidence(
            extension(ByteArray(32) { 9 }), challenge))

    @Test fun missingOrWrongLengthChallengeIsDenied() {
        assertFalse(OwnerAttestationChallenge.matchesLocalEvidence(null, challenge))
        assertFalse(OwnerAttestationChallenge.matchesLocalEvidence(extension(), byteArrayOf(1)))
    }

    @Test fun teeOnlyAttestationIsDenied() =
        assertFalse(OwnerAttestationChallenge.matchesLocalEvidence(
            extension(attestationLevel = 1), challenge))

    @Test fun teeOnlyKeymasterIsDenied() =
        assertFalse(OwnerAttestationChallenge.matchesLocalEvidence(
            extension(keymasterLevel = 1), challenge))

    @Test fun trailingBytesAndTruncationAreDenied() {
        val valid = extension()
        assertFalse(OwnerAttestationChallenge.matchesLocalEvidence(valid + 0, challenge))
        assertFalse(OwnerAttestationChallenge.matchesLocalEvidence(
            valid.copyOf(valid.size - 1), challenge))
    }

    @Test fun indefiniteAndNonMinimalLengthsAreDenied() {
        val valid = extension()
        assertFalse(OwnerAttestationChallenge.matchesLocalEvidence(
            byteArrayOf(4, 0x80.toByte()) + valid.drop(2).toByteArray(), challenge))
        assertFalse(OwnerAttestationChallenge.matchesLocalEvidence(
            byteArrayOf(4, 0x81.toByte(), (valid.size - 2).toByte()) +
                valid.drop(2).toByteArray(), challenge))
    }

    @Test fun negativeAttestationVersionsAreDenied() {
        val valid = extension()
        val prefix = byteArrayOf(0x02, 0x01, 0x04)
        val index = valid.indices.firstOrNull { i ->
            i + prefix.size <= valid.size && valid.copyOfRange(i, i + prefix.size).contentEquals(prefix)
        } ?: throw AssertionError("version field absent")
        val negative = valid.clone()
        negative[index + 2] = 0xff.toByte()
        assertFalse(OwnerAttestationChallenge.matchesLocalEvidence(negative, challenge))
    }

    @Test fun oversizedAndWrongTagAreDenied() {
        assertFalse(OwnerAttestationChallenge.matchesLocalEvidence(ByteArray(8193), challenge))
        val invalid = extension().clone()
        invalid[0] = 0x30
        assertFalse(OwnerAttestationChallenge.matchesLocalEvidence(invalid, challenge))
    }
}
