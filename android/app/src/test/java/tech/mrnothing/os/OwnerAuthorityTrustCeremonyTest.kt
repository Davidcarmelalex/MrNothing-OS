package tech.mrnothing.os

import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.Signature
import java.security.Security
import java.util.Base64
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

/** Pure JDK policy tests; no Android Keystore, network, UI or Pixel is exercised. */
class OwnerAuthorityTrustCeremonyTest {
    private fun keyPair(): KeyPair = KeyPairGenerator.getInstance("Ed25519").generateKeyPair()

    private fun candidate(
        pair: KeyPair,
        generation: Long = 1L,
        keyId: String = "authority-1"
    ) = AuthorityTrustCandidate(keyId, generation, pair.public.encoded)

    private fun fingerprint(candidate: AuthorityTrustCandidate): String =
        OwnerAuthorityTrustCeremony.fingerprintForOwner(candidate.publicKeySpkiDer)!!

    private fun ready(decision: AuthorityTrustDecision): AuthorityTrustDecision.Ready {
        assertTrue("Expected Ready but got " + decision, decision is AuthorityTrustDecision.Ready)
        return decision as AuthorityTrustDecision.Ready
    }

    private fun blocked(decision: AuthorityTrustDecision, reason: AuthorityTrustBlockReason) {
        assertTrue("Expected Blocked but got " + decision, decision is AuthorityTrustDecision.Blocked)
        assertEquals(reason, (decision as AuthorityTrustDecision.Blocked).reason)
    }

    private fun sign(oldAuthority: KeyPair, next: AuthorityTrustCandidate): ByteArray {
        val payload = OwnerAuthorityTrustCeremony.rotationPayload(next)
        assertNotNull(payload)
        return Signature.getInstance("Ed25519").run {
            initSign(oldAuthority.private)
            update(payload)
            sign()
        }
    }

    private fun firstInstall(pair: KeyPair): AuthorityTrustRecord {
        val candidate = candidate(pair)
        return ready(OwnerAuthorityTrustCeremony.prepareFirstInstall(
            candidate, fingerprint(candidate), true, 0L
        )).record
    }

    @Test fun fingerprintIsCanonicalAndBoundToExactSpkiBytes() {
        val candidate = candidate(keyPair())
        val fingerprint = fingerprint(candidate)
        assertTrue(Regex("^SHA256:[0-9A-F]{64}$").matches(fingerprint))
        assertEquals(fingerprint,
            OwnerAuthorityTrustCeremony.fingerprintForOwner(candidate.publicKeySpkiDer))
        assertNull(OwnerAuthorityTrustCeremony.fingerprintForOwner(byteArrayOf(1, 2, 3)))
    }

    @Test fun rfc8032PublicKeyImportsWithoutGlobalProviderMutation() {
        val providersBefore = Security.getProviders().map { it.name }
        val spki = Base64.getDecoder().decode(
            "MCowBQYDK2VwAyEA11qYAYKxCrfVS/7TyWQHOg7hcvPapiMlrwIaaPcHURo="
        )
        assertEquals(
            "SHA256:06E3FD8FDA29BB60AB59557DE61EDB0AECDB231134BE30E75B455F8E1B792FA9",
            OwnerAuthorityTrustCeremony.fingerprintForOwner(spki)
        )
        assertEquals(providersBefore, Security.getProviders().map { it.name })
    }

    @Test fun firstInstallRequiresOutOfBandFingerprintAndOwnerConfirmation() {
        val candidate = candidate(keyPair())
        ready(OwnerAuthorityTrustCeremony.prepareFirstInstall(
            candidate, fingerprint(candidate), true, 0L
        ))
        blocked(OwnerAuthorityTrustCeremony.prepareFirstInstall(
            candidate, "SHA256:" + "0".repeat(64), true, 0L
        ), AuthorityTrustBlockReason.OUT_OF_BAND_FINGERPRINT_MISMATCH)
        blocked(OwnerAuthorityTrustCeremony.prepareFirstInstall(
            candidate, fingerprint(candidate), false, 0L
        ), AuthorityTrustBlockReason.OWNER_CONFIRMATION_REQUIRED)
    }

    @Test fun firstInstallRequiresEmptyMarkerAndGenerationOne() {
        val candidate = candidate(keyPair())
        blocked(OwnerAuthorityTrustCeremony.prepareFirstInstall(
            candidate, fingerprint(candidate), true, 1L
        ), AuthorityTrustBlockReason.INITIAL_STATE_ALREADY_EXISTS)
        blocked(OwnerAuthorityTrustCeremony.prepareFirstInstall(
            candidate.copy(generation = 2L), fingerprint(candidate), true, 0L
        ), AuthorityTrustBlockReason.INITIAL_GENERATION_MUST_BE_ONE)
    }

    @Test fun malformedKeyAndKeyIdAreRejected() {
        blocked(OwnerAuthorityTrustCeremony.prepareFirstInstall(
            AuthorityTrustCandidate("bad key id", 1L, candidate(keyPair()).publicKeySpkiDer),
            "SHA256:" + "0".repeat(64), true, 0L
        ), AuthorityTrustBlockReason.INVALID_CANDIDATE)
        blocked(OwnerAuthorityTrustCeremony.prepareFirstInstall(
            AuthorityTrustCandidate("authority-1", 1L, byteArrayOf(1, 2, 3)),
            "SHA256:" + "0".repeat(64), true, 0L
        ), AuthorityTrustBlockReason.INVALID_CANDIDATE)
    }

    @Test fun rotationRequiresCurrentAuthoritySignatureAndNextGeneration() {
        val old = keyPair()
        val current = firstInstall(old)
        val next = candidate(keyPair(), 2L, "authority-2")
        val accepted = ready(OwnerAuthorityTrustCeremony.prepareRotation(
            current, next, sign(old, next), fingerprint(next), true, 1L
        ))
        assertEquals(AuthorityTrustMode.ROTATION, accepted.mode)
        assertEquals(2L, accepted.record.generation)
    }

    @Test fun rotationRejectsWrongSignerAndTamperedSignature() {
        val old = keyPair()
        val current = firstInstall(old)
        val next = candidate(keyPair(), 2L, "authority-2")
        blocked(OwnerAuthorityTrustCeremony.prepareRotation(
            current, next, sign(keyPair(), next), fingerprint(next), true, 1L
        ), AuthorityTrustBlockReason.ROTATION_SIGNATURE_INVALID)
        val tampered = sign(old, next).also { it[0] = (it[0].toInt() xor 1).toByte() }
        blocked(OwnerAuthorityTrustCeremony.prepareRotation(
            current, next, tampered, fingerprint(next), true, 1L
        ), AuthorityTrustBlockReason.ROTATION_SIGNATURE_INVALID)
    }

    @Test fun rotationRejectsFingerprintMismatchAndMissingOwnerConfirmation() {
        val old = keyPair()
        val current = firstInstall(old)
        val next = candidate(keyPair(), 2L, "authority-2")
        val signature = sign(old, next)
        blocked(OwnerAuthorityTrustCeremony.prepareRotation(
            current, next, signature, "SHA256:" + "0".repeat(64), true, 1L
        ), AuthorityTrustBlockReason.OUT_OF_BAND_FINGERPRINT_MISMATCH)
        blocked(OwnerAuthorityTrustCeremony.prepareRotation(
            current, next, signature, fingerprint(next), false, 1L
        ), AuthorityTrustBlockReason.OWNER_CONFIRMATION_REQUIRED)
    }

    @Test fun rotationRejectsRollbackSkippedGenerationAndMarkerMismatch() {
        val old = keyPair()
        val current = firstInstall(old)
        val next = candidate(keyPair(), 2L, "authority-2")
        val signature = sign(old, next)
        blocked(OwnerAuthorityTrustCeremony.prepareRotation(
            current, next.copy(generation = 1L), signature, fingerprint(next), true, 1L
        ), AuthorityTrustBlockReason.NEXT_GENERATION_REQUIRED)
        blocked(OwnerAuthorityTrustCeremony.prepareRotation(
            current, next.copy(generation = 3L), signature, fingerprint(next), true, 1L
        ), AuthorityTrustBlockReason.NEXT_GENERATION_REQUIRED)
        blocked(OwnerAuthorityTrustCeremony.prepareRotation(
            current, next, signature, fingerprint(next), true, 0L
        ), AuthorityTrustBlockReason.GENERATION_MARKER_MISMATCH)
        blocked(OwnerAuthorityTrustCeremony.prepareRotation(
            current, next, signature, fingerprint(next), true, 2L
        ), AuthorityTrustBlockReason.GENERATION_MARKER_MISMATCH)
    }

    @Test fun rotationRequiresAChangedKeyAndKeyId() {
        val old = keyPair()
        val current = firstInstall(old)
        val sameKeyNewId = candidate(old, 2L, "authority-2")
        blocked(OwnerAuthorityTrustCeremony.prepareRotation(
            current, sameKeyNewId, sign(old, sameKeyNewId),
            fingerprint(sameKeyNewId), true, 1L
        ), AuthorityTrustBlockReason.AUTHORITY_KEY_MUST_CHANGE)
        val newKeySameId = candidate(keyPair(), 2L, "authority-1")
        blocked(OwnerAuthorityTrustCeremony.prepareRotation(
            current, newKeySameId, sign(old, newKeySameId),
            fingerprint(newKeySameId), true, 1L
        ), AuthorityTrustBlockReason.AUTHORITY_KEY_MUST_CHANGE)
    }

    @Test fun invalidCurrentRecordCannotAuthorizeRotation() {
        val old = keyPair()
        val current = firstInstall(old).copy(fingerprint = "SHA256:" + "0".repeat(64))
        val next = candidate(keyPair(), 2L, "authority-2")
        blocked(OwnerAuthorityTrustCeremony.prepareRotation(
            current, next, sign(old, next), fingerprint(next), true, 1L
        ), AuthorityTrustBlockReason.INVALID_ACTIVE_RECORD)
    }

    @Test fun recoveryRequiresExistingWatermarkAndMissingActiveRecord() {
        val next = candidate(keyPair(), 6L, "authority-recovery")
        ready(OwnerAuthorityTrustCeremony.prepareRecovery(
            next, fingerprint(next), true, 5L, false
        ))
        blocked(OwnerAuthorityTrustCeremony.prepareRecovery(
            next, fingerprint(next), true, 0L, false
        ), AuthorityTrustBlockReason.RECOVERY_NOT_ELIGIBLE)
        blocked(OwnerAuthorityTrustCeremony.prepareRecovery(
            next, fingerprint(next), true, 5L, true
        ), AuthorityTrustBlockReason.RECOVERY_NOT_ELIGIBLE)
    }

    @Test fun recoveryRequiresExactlyNextGenerationAndOwnerFingerprint() {
        val next = candidate(keyPair(), 6L, "authority-recovery")
        blocked(OwnerAuthorityTrustCeremony.prepareRecovery(
            next.copy(generation = 5L), fingerprint(next), true, 5L, false
        ), AuthorityTrustBlockReason.NEXT_GENERATION_REQUIRED)
        blocked(OwnerAuthorityTrustCeremony.prepareRecovery(
            next.copy(generation = 7L), fingerprint(next), true, 5L, false
        ), AuthorityTrustBlockReason.NEXT_GENERATION_REQUIRED)
        blocked(OwnerAuthorityTrustCeremony.prepareRecovery(
            next, "SHA256:" + "0".repeat(64), true, 5L, false
        ), AuthorityTrustBlockReason.OUT_OF_BAND_FINGERPRINT_MISMATCH)
        blocked(OwnerAuthorityTrustCeremony.prepareRecovery(
            next, fingerprint(next), false, 5L, false
        ), AuthorityTrustBlockReason.OWNER_CONFIRMATION_REQUIRED)
    }

    @Test fun generationExhaustionFailsClosed() {
        val next = candidate(keyPair(), Long.MAX_VALUE, "authority-max")
        blocked(OwnerAuthorityTrustCeremony.prepareRecovery(
            next, fingerprint(next), true, Long.MAX_VALUE, false
        ), AuthorityTrustBlockReason.GENERATION_EXHAUSTED)
        val old = keyPair()
        val current = firstInstall(old).copy(generation = Long.MAX_VALUE)
        blocked(OwnerAuthorityTrustCeremony.prepareRotation(
            current, next, ByteArray(64), fingerprint(next), true, Long.MAX_VALUE
        ), AuthorityTrustBlockReason.GENERATION_EXHAUSTED)
    }

    @Test fun malformedFingerprintAndNonCanonicalCaseAreRejected() {
        val candidate = candidate(keyPair())
        blocked(OwnerAuthorityTrustCeremony.prepareFirstInstall(
            candidate, fingerprint(candidate).lowercase(), true, 0L
        ), AuthorityTrustBlockReason.OUT_OF_BAND_FINGERPRINT_MISMATCH)
        blocked(OwnerAuthorityTrustCeremony.prepareFirstInstall(
            candidate, "not-a-fingerprint", true, 0L
        ), AuthorityTrustBlockReason.OUT_OF_BAND_FINGERPRINT_MISMATCH)
    }

    @Test fun rotationPayloadIsDeterministicAndChangesWithCandidate() {
        val first = candidate(keyPair(), 2L, "authority-2")
        val second = candidate(keyPair(), 2L, "authority-2")
        val payload = OwnerAuthorityTrustCeremony.rotationPayload(first)
        assertNotNull(payload)
        assertTrue(payload!!.contentEquals(OwnerAuthorityTrustCeremony.rotationPayload(first)!!))
        assertFalse(payload.contentEquals(OwnerAuthorityTrustCeremony.rotationPayload(second)!!))
    }
}
