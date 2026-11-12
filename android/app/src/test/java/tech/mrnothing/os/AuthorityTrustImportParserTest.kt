package tech.mrnothing.os

import java.security.KeyPair
import java.security.KeyPairGenerator
import java.util.Base64
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class AuthorityTrustImportParserTest {
    private fun pair(): KeyPair = KeyPairGenerator.getInstance("Ed25519").generateKeyPair()
    private fun base64(bytes: ByteArray): String = Base64.getEncoder().encodeToString(bytes)

    private fun validInput(): Triple<KeyPair, String, AuthorityTrustImportParseResult> {
        val pair = pair()
        val spki = base64(pair.public.encoded)
        val fingerprint = OwnerAuthorityTrustCeremony.fingerprintForOwner(pair.public.encoded)!!
        val result = AuthorityTrustImportParser.parse(
            "authority-1", "1", spki, "", fingerprint
        )
        return Triple(pair, fingerprint, result)
    }

    @Test fun acceptsCanonicalEd25519SpkiAndMatchingIndependentFingerprint() {
        val (_, fingerprint, result) = validInput()
        assertTrue(result is AuthorityTrustImportParseResult.Valid)
        val parsed = (result as AuthorityTrustImportParseResult.Valid).value
        assertEquals(fingerprint, parsed.computedFingerprint)
        assertEquals(1L, parsed.candidate.generation)
        assertTrue(parsed.rotationSignature.isEmpty())
        assertNotNull(parsed.inputBinding)
    }

    @Test fun rejectsFingerprintMismatch() {
        val (pair, _, _) = validInput()
        val wrong = "SHA256:" + "0".repeat(64)
        val result = AuthorityTrustImportParser.parse(
            "authority-1", "1", base64(pair.public.encoded), "", wrong
        )
        assertEquals(
            AuthorityTrustImportError.FINGERPRINT_MISMATCH,
            (result as AuthorityTrustImportParseResult.Invalid).reason
        )
    }

    @Test fun rejectsNonCanonicalBase64Whitespace() {
        val (pair, fingerprint, _) = validInput()
        val result = AuthorityTrustImportParser.parse(
            "authority-1", "1", base64(pair.public.encoded) + "\n", "", fingerprint
        )
        assertEquals(
            AuthorityTrustImportError.INVALID_PUBLIC_KEY_BASE64,
            (result as AuthorityTrustImportParseResult.Invalid).reason
        )
    }

    @Test fun rejectsLeadingZeroGeneration() {
        val (pair, fingerprint, _) = validInput()
        val result = AuthorityTrustImportParser.parse(
            "authority-1", "01", base64(pair.public.encoded), "", fingerprint
        )
        assertEquals(
            AuthorityTrustImportError.INVALID_GENERATION,
            (result as AuthorityTrustImportParseResult.Invalid).reason
        )
    }

    @Test fun rejectsInvalidRotationSignatureLength() {
        val (pair, fingerprint, _) = validInput()
        val result = AuthorityTrustImportParser.parse(
            "authority-1", "1", base64(pair.public.encoded), base64(ByteArray(63)), fingerprint
        )
        assertEquals(
            AuthorityTrustImportError.INVALID_ROTATION_SIGNATURE,
            (result as AuthorityTrustImportParseResult.Invalid).reason
        )
    }

    @Test fun rejectsMalformedEd25519Spki() {
        val result = AuthorityTrustImportParser.parse(
            "authority-1", "1", base64(byteArrayOf(1, 2, 3)), "",
            "SHA256:" + "0".repeat(64)
        )
        assertEquals(
            AuthorityTrustImportError.INVALID_PUBLIC_KEY,
            (result as AuthorityTrustImportParseResult.Invalid).reason
        )
    }

    @Test fun confirmationBindingChangesWithModeAndStoreSnapshot() {
        val first = AuthorityTrustImportParser.confirmationBinding(
            AuthorityTrustMode.FIRST_INSTALL, "EMPTY", "same-input"
        )
        val rotation = AuthorityTrustImportParser.confirmationBinding(
            AuthorityTrustMode.ROTATION, "ACTIVE|1", "same-input"
        )
        val changed = AuthorityTrustImportParser.confirmationBinding(
            AuthorityTrustMode.FIRST_INSTALL, "EMPTY", "changed-input"
        )
        assertTrue(first != rotation)
        assertTrue(first != changed)
    }
}
